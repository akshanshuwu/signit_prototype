"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { makeAudioBuffer, type PlaybackData } from "../lib/dsp/playback";

export type PlayStatus = "idle" | "ready" | "playing" | "paused" | "ended";

export interface PlaybackSync {
  status: PlayStatus;
  currentTime: number;
  duration: number;
  volume: number;
  muted: boolean;
  analyserRef: React.RefObject<AnalyserNode | null>;
  /** Sample-accurate clock for canvases (no React render per frame). */
  getTime: () => number;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (sec: number) => void;
  setVolume: (v: number) => void;
  toggleMute: () => void;
}

/**
 * Owns AudioContext + BufferSource + Analyser + Gain for one capture.
 * Clock: posSec = offset + (ctx.currentTime - t0), so the playhead is
 * tied to the real audio clock — never a fake timer.
 */
export function usePlaybackSync(data: PlaybackData | null): PlaybackSync {
  const [status, setStatus] = useState<PlayStatus>("idle");
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolumeState] = useState(0.9);
  const [muted, setMuted] = useState(false);

  const ctxRef = useRef<AudioContext | null>(null);
  const srcRef = useRef<AudioBufferSourceNode | null>(null);
  const gainRef = useRef<GainNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const bufRef = useRef<AudioBuffer | null>(null);
  const t0Ref = useRef(0);
  const offRef = useRef(0);
  const rafRef = useRef(0);
  const statusRef = useRef<PlayStatus>("idle");
  const lastUiRef = useRef(0);

  const duration = data ? data.mono.length / data.sampleRate : 0;

  function setStatusBoth(s: PlayStatus) {
    statusRef.current = s;
    setStatus(s);
  }

  const getTime = useCallback(() => {
    const ctx = ctxRef.current;
    if (!ctx || !bufRef.current) return offRef.current;
    if (statusRef.current === "playing") {
      return Math.min(
        bufRef.current.duration,
        offRef.current + (ctx.currentTime - t0Ref.current)
      );
    }
    return offRef.current;
  }, []);

  // Tick loop: updates the time label ~10Hz; canvases read getTime() directly.
  useEffect(() => {
    function tick() {
      const t = getTime();
      const now = performance.now();
      if (now - lastUiRef.current > 100) {
        lastUiRef.current = now;
        setCurrentTime(t);
      }
      if (statusRef.current === "playing") rafRef.current = requestAnimationFrame(tick);
    }
    if (status === "playing") rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [status, getTime]);

  function ensureCtx(): AudioContext {
    let ctx = ctxRef.current;
    if (!ctx) {
      const Ctx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      ctx = new Ctx();
      ctxRef.current = ctx;
      const gain = ctx.createGain();
      gain.gain.value = muted ? 0 : volume;
      gainRef.current = gain;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.8;
      analyserRef.current = analyser;
      gain.connect(analyser);
      analyser.connect(ctx.destination);
    }
    if (ctx.state === "suspended") void ctx.resume();
    return ctx;
  }

  function startSource(at: number) {
    const ctx = ensureCtx();
    if (!data || !gainRef.current) return;
    if (!bufRef.current) bufRef.current = makeAudioBuffer(ctx, data);
    try { srcRef.current?.stop(); } catch { /* already stopped */ }
    srcRef.current?.disconnect();
    const src = ctx.createBufferSource();
    src.buffer = bufRef.current;
    src.connect(gainRef.current);
    src.onended = () => {
      // Ignore onended from manual stop/seek (a newer source exists).
      if (srcRef.current !== src) return;
      if (statusRef.current === "playing") {
        offRef.current = bufRef.current?.duration ?? offRef.current;
        setCurrentTime(offRef.current);
        setStatusBoth("ended");
      }
    };
    srcRef.current = src;
    offRef.current = Math.max(0, Math.min(at, bufRef.current.duration - 0.01));
    t0Ref.current = ctx.currentTime;
    src.start(0, offRef.current);
    setStatusBoth("playing");
  }

  const play = useCallback(() => {
    if (!data) return;
    const st = statusRef.current;
    if (st === "playing") return;
    // Rebuild buffer if the file changed since last play.
    if (bufRef.current && Math.abs(bufRef.current.duration - duration) > 0.05) {
      bufRef.current = null;
    }
    const at = st === "ended" ? 0 : offRef.current;
    startSource(at);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, duration]);

  const pause = useCallback(() => {
    if (statusRef.current !== "playing") return;
    offRef.current = getTime();
    setCurrentTime(offRef.current);
    try { srcRef.current?.stop(); } catch { /* noop */ }
    setStatusBoth("paused");
  }, [getTime]);

  const toggle = useCallback(() => {
    if (statusRef.current === "playing") pause();
    else play();
  }, [pause, play]);

  const seek = useCallback(
    (sec: number) => {
      if (!data || !bufRef.current && statusRef.current !== "playing" && !ctxRef.current) {
        // No context yet — just stage the offset for first play.
        offRef.current = Math.max(0, Math.min(sec, duration));
        setCurrentTime(offRef.current);
        if (statusRef.current === "idle" && duration > 0) setStatusBoth("ready");
        return;
      }
      const clamped = Math.max(0, Math.min(sec, duration));
      if (statusRef.current === "playing") startSource(clamped);
      else {
        offRef.current = clamped;
        setCurrentTime(clamped);
        if (statusRef.current === "ended" && clamped < duration) setStatusBoth("paused");
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, duration]
  );

  const setVolume = useCallback((v: number) => {
    const nv = Math.max(0, Math.min(1, v));
    setVolumeState(nv);
    if (nv > 0) setMuted(false);
    const ctx = ctxRef.current;
    const gain = gainRef.current;
    if (ctx && gain) gain.gain.setTargetAtTime(nv, ctx.currentTime, 0.02);
  }, []);

  const toggleMute = useCallback(() => {
    const ctx = ctxRef.current;
    const gain = gainRef.current;
    setMuted((m) => {
      const nm = !m;
      if (ctx && gain) gain.gain.setTargetAtTime(nm ? 0 : volume, ctx.currentTime, 0.02);
      return nm;
    });
  }, [volume]);

  // Reset when the file changes.
  useEffect(() => {
    try { srcRef.current?.stop(); } catch { /* noop */ }
    srcRef.current?.disconnect();
    srcRef.current = null;
    bufRef.current = null;
    offRef.current = 0;
    setCurrentTime(0);
    setStatusBoth(data && duration > 0 ? "ready" : "idle");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, duration]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current);
      try { srcRef.current?.stop(); } catch { /* noop */ }
      srcRef.current?.disconnect();
      void ctxRef.current?.close().catch(() => {});
      ctxRef.current = null;
    };
  }, []);

  return {
    status,
    currentTime,
    duration,
    volume,
    muted,
    analyserRef,
    getTime,
    play,
    pause,
    toggle,
    seek,
    setVolume,
    toggleMute,
  };
}
