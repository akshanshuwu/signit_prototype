"use client";

import { useEffect, useRef } from "react";

const WINDOW = 512;

/**
 * Sliding I/Q window around the real playback position.
 * Redraws at most ~15fps while playing; frozen frame when paused.
 * For .wav the Q lane is zeros (I-only scatter) — labelled honestly.
 */
export default function ConstellationLiveCanvas({
  i,
  q,
  fs,
  getTime,
  playing,
}: {
  i: Float32Array;
  q: Float32Array;
  fs: number;
  getTime: () => number;
  playing: boolean;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ getTime, playing });
  stateRef.current = { getTime, playing };
  const dataRef = useRef({ i, q, fs });
  dataRef.current = { i, q, fs };

  useEffect(() => {
    const wrapOrNull = wrapRef.current;
    const canvasOrNull = canvasRef.current;
    if (!wrapOrNull || !canvasOrNull) return;
    const ctxOrNull = canvasOrNull.getContext("2d");
    if (!ctxOrNull) return;
    const wr: HTMLDivElement = wrapOrNull;
    const c: HTMLCanvasElement = canvasOrNull;
    const ctx: CanvasRenderingContext2D = ctxOrNull;

    const dpr = Math.min(2, window.devicePixelRatio || 1);
    function size() {
      const rect = wr.getBoundingClientRect();
      const w = Math.max(1, Math.floor(rect.width));
      const h = 180;
      c.width = Math.floor(w * dpr);
      c.height = Math.floor(h * dpr);
      c.style.width = `${w}px`;
      c.style.height = `${h}px`;
    }
    size();
    const ro = new ResizeObserver(size);
    ro.observe(wr);

    let raf = 0;
    let lastDraw = 0;
    function frame(now: number) {
      const { getTime: gt, playing: pl } = stateRef.current;
      if (pl && now - lastDraw > 66) {
        lastDraw = now;
        const { i: ii, q: qq, fs: ffs } = dataRef.current;
        const pos = Math.floor(gt() * ffs);
        const end = Math.max(WINDOW, Math.min(ii.length, pos + Math.floor(WINDOW / 2)));
        const start = Math.max(0, end - WINDOW);
        const w = c.width / dpr;
        const h = c.height / dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, w, h);
        // Axes
        ctx.strokeStyle = "#E7E0D3";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, h / 2);
        ctx.lineTo(w, h / 2);
        ctx.moveTo(w / 2, 0);
        ctx.lineTo(w / 2, h);
        ctx.stroke();
        // Square mapping over [-1, 1]
        const s = Math.min(w, h) / 2 - 8;
        const cx = w / 2;
        const cy = h / 2;
        ctx.fillStyle = "#0E7C6B";
        for (let k = start; k < end; k++) {
          const x = cx + ii[k] * s;
          const y = cy - qq[k] * s;
          ctx.fillRect(x - 1, y - 1, 2, 2);
        }
        ctx.fillStyle = "#6B7280";
        ctx.font = "10px 'IBM Plex Mono', monospace";
        ctx.fillText(`LIVE WINDOW · ${end - start} SYM @ ${gt().toFixed(1)}s`, 8, 14);
      }
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  return (
    <div ref={wrapRef} className="w-full min-w-0 overflow-hidden rounded-md border border-line bg-white">
      <canvas ref={canvasRef} className="block w-full" role="img" aria-label="Live constellation window" />
    </div>
  );
}
