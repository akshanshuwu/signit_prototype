"use client";

import { useEffect, useRef } from "react";

const BARS = 48;

/**
 * Live output spectrum fed by AnalyserNode FFT (2048).
 * Redraws only while playing — when paused the last frame stays
 * (honest freeze, not animation).
 */
export default function LiveSpectrumCanvas({
  analyserRef,
  playing,
}: {
  analyserRef: React.RefObject<AnalyserNode | null>;
  playing: boolean;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ playing });
  stateRef.current = { playing };

  useEffect(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;
    const ctxOrNull = canvas.getContext("2d");
    if (!ctxOrNull) return;
    // Non-null locals so closures keep narrowing under strict mode.
    const c: HTMLCanvasElement = canvas;
    const wr: HTMLDivElement = wrap;
    const ctx: CanvasRenderingContext2D = ctxOrNull;

    const dpr = Math.min(2, window.devicePixelRatio || 1);
    function size() {
      const rect = wr.getBoundingClientRect();
      const w = Math.max(1, Math.floor(rect.width));
      const h = 120;
      c.width = Math.floor(w * dpr);
      c.height = Math.floor(h * dpr);
      c.style.width = `${w}px`;
      c.style.height = `${h}px`;
    }
    size();
    const ro = new ResizeObserver(size);
    ro.observe(wr);

    const data = new Float32Array(analyserRef.current?.frequencyBinCount ?? 1024);
    let raf = 0;

    function drawIdle() {
      const w = c.width / dpr;
      const h = c.height / dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#6B7280";
      ctx.font = "11px 'IBM Plex Mono', monospace";
      ctx.fillText("Press play — live spectrum appears here", 12, 22);
      ctx.strokeStyle = "#E7E0D3";
      ctx.beginPath();
      ctx.moveTo(0, h - 1);
      ctx.lineTo(w, h - 1);
      ctx.stroke();
    }

    function frame() {
      const an = analyserRef.current;
      if (!stateRef.current.playing || !an) {
        raf = requestAnimationFrame(frame);
        return;
      }
      if (data.length !== an.frequencyBinCount) {
        raf = requestAnimationFrame(frame);
        return;
      }
      an.getFloatFrequencyData(data);
      const w = c.width / dpr;
      const h = c.height / dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      // Map -100..-30 dB to 0..1 over the first ~1/3 bins (audible band).
      const use = Math.floor(data.length / 3);
      const bw = w / BARS;
      for (let b = 0; b < BARS; b++) {
        const idx = Math.floor((b / BARS) * use);
        const db = data[idx] ?? -100;
        const v = Math.max(0, Math.min(1, (db + 100) / 70));
        const bh = Math.max(2, v * (h - 18));
        ctx.fillStyle = b % 4 === 0 ? "#0E7C6B" : "#16A34A";
        const x = b * bw + bw * 0.2;
        ctx.fillRect(x, h - 8 - bh, bw * 0.6, bh);
      }
      ctx.fillStyle = "#6B7280";
      ctx.font = "10px 'IBM Plex Mono', monospace";
      ctx.fillText("LIVE OUTPUT SPECTRUM", 8, 14);
      raf = requestAnimationFrame(frame);
    }

    drawIdle();
    raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [analyserRef]);

  return (
    <div ref={wrapRef} className="w-full min-w-0 overflow-hidden rounded-md border border-line bg-white">
      <canvas ref={canvasRef} className="block w-full" role="img" aria-label="Live spectrum analyzer" />
    </div>
  );
}
