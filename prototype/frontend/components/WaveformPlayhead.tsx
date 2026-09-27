"use client";

import { useEffect, useRef } from "react";

/**
 * Waveform overview with a playhead tied to the real audio clock.
 * Peaks are drawn once to an offscreen canvas; per frame we blit +
 * shade played region + draw the cursor. Click/drag seeks.
 */
export default function WaveformPlayhead({
  peaks,
  duration,
  getTime,
  playing,
  onSeek,
}: {
  peaks: Float32Array;
  duration: number;
  getTime: () => number;
  playing: boolean;
  onSeek: (sec: number) => void;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const offRef = useRef<HTMLCanvasElement | null>(null);
  const dragRef = useRef(false);
  const stateRef = useRef({ getTime, playing, onSeek, duration });
  stateRef.current = { getTime, playing, onSeek, duration };

  // Render static peaks to offscreen when data/size changes.
  useEffect(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const rect = wrap.getBoundingClientRect();
    const w = Math.max(1, Math.floor(rect.width));
    const h = 96;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;

    const off = document.createElement("canvas");
    off.width = canvas.width;
    off.height = canvas.height;
    const g = off.getContext("2d");
    if (g) {
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.clearRect(0, 0, w, h);
      const mid = h / 2;
      g.fillStyle = "#0E7C6B";
      const n = peaks.length;
      const bw = w / n;
      for (let k = 0; k < n; k++) {
        const bh = Math.max(1, peaks[k] * (h / 2 - 6));
        const x = k * bw;
        g.fillRect(x, mid - bh, Math.max(1, bw * 0.8), bh * 2);
      }
      g.strokeStyle = "#E7E0D3";
      g.lineWidth = 1;
      g.beginPath();
      g.moveTo(0, mid);
      g.lineTo(w, mid);
      g.stroke();
    }
    offRef.current = off;
  }, [peaks]);

  // Playhead loop — canvas only, no React state per frame.
  useEffect(() => {
    const canvasOrNull = canvasRef.current;
    if (!canvasOrNull) return;
    const ctxOrNull = canvasOrNull.getContext("2d");
    if (!ctxOrNull) return;
    // Non-null locals so closures keep narrowing under strict mode.
    const c: HTMLCanvasElement = canvasOrNull;
    const ctx: CanvasRenderingContext2D = ctxOrNull;
    let raf = 0;
    function frame() {
      const { getTime: gt, duration: dur } = stateRef.current;
      const off = offRef.current;
      if (off) {
        const dpr = Math.min(2, window.devicePixelRatio || 1);
        const w = c.width / dpr;
        const h = c.height / dpr;
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, c.width, c.height);
        ctx.drawImage(off, 0, 0);
        // Played shading + cursor
        const t = gt();
        const p = dur > 0 ? Math.max(0, Math.min(1, t / dur)) : 0;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.fillStyle = "rgba(14,124,107,0.12)";
        ctx.fillRect(0, 0, w * p, h);
        ctx.fillStyle = "#0E7C6B";
        ctx.fillRect(w * p - 1, 0, 2, h);
      }
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, []);

  function seekFromEvent(e: React.PointerEvent) {
    const wrap = wrapRef.current;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const p = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    stateRef.current.onSeek(p * stateRef.current.duration);
  }

  return (
    <div
      ref={wrapRef}
      className="w-full min-w-0 cursor-crosshair overflow-hidden rounded-md border border-line bg-white"
      onPointerDown={(e) => {
        dragRef.current = true;
        (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
        seekFromEvent(e);
      }}
      onPointerMove={(e) => {
        if (dragRef.current) seekFromEvent(e);
      }}
      onPointerUp={() => {
        dragRef.current = false;
      }}
      role="slider"
      aria-label="Waveform seek"
      aria-valuemin={0}
      aria-valuemax={Math.round(duration)}
      aria-valuenow={Math.round(getTime())}
      tabIndex={0}
      onKeyDown={(e) => {
        const t = getTime();
        if (e.key === "ArrowRight") onSeek(Math.min(duration, t + 1));
        if (e.key === "ArrowLeft") onSeek(Math.max(0, t - 1));
      }}
    >
      <canvas ref={canvasRef} className="block w-full" />
    </div>
  );
}
