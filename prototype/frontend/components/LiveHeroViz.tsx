"use client";

import { useEffect, useRef } from "react";

interface Props {
  /** demo: procedural animated signal. file: render provided waveform (used in later phases). */
  mode?: "demo" | "file";
  waveform?: Float32Array | null;
  className?: string;
}

const BARS = 32;

/**
 * Canvas-only live signal visual: waveform strip + frequency bars.
 * No dependencies, no fake playback linkage — demo mode is an ambient
 * procedural signal; file mode draws the real uploaded waveform peaks.
 */
export default function LiveHeroViz({ mode = "demo", waveform = null, className = "" }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const wrap = wrapRef.current;
    if (!canvas || !wrap) return;

    const ctxOrNull = canvas.getContext("2d");
    if (!ctxOrNull) return;
    // Non-null locals so closures keep narrowing under strict mode.
    const c: HTMLCanvasElement = canvas;
    const wr: HTMLDivElement = wrap;
    const ctx: CanvasRenderingContext2D = ctxOrNull;

    let raf = 0;
    let running = true;
    let w = 0;
    let h = 0;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function resize() {
      const rect = wr.getBoundingClientRect();
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      w = Math.max(1, Math.floor(rect.width));
      h = 204;
      c.width = Math.floor(w * dpr);
      c.height = Math.floor(h * dpr);
      c.style.width = `${w}px`;
      c.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(wr);

    const io = new IntersectionObserver(
      (entries) => {
        running = entries[0]?.isIntersecting !== false;
        if (running && !reduced) loop(performance.now());
      },
      { threshold: 0.05 }
    );
    io.observe(wr);

    // Banded layout with real padding so strokes, labels and bars
    // never touch each other or the container edges.
    const PAD_X = 12;
    const WAVE_LABEL_Y = 16;
    const WAVE_TOP = 24;
    const WAVE_MID = 58;
    const WAVE_AMP = 28;
    const WAVE_BASE = 94;
    const DIVIDER_Y = 106;
    const SPEC_LABEL_Y = 124;
    const BAR_TOP = 132;
    const BAR_BASE = 192;

    function drawDemo(t: number) {
      const ts = t / 1000;
      const x0 = PAD_X;
      const x1 = w - PAD_X;

      ctx.clearRect(0, 0, w, h);

      // Labels first (own reserved bands, never overlapped by signal).
      ctx.fillStyle = "#6B7280";
      ctx.font = "10px 'IBM Plex Mono', monospace";
      ctx.fillText("WAVEFORM", x0, WAVE_LABEL_Y);
      ctx.fillText("SPECTRUM · 32 BIN", x0, SPEC_LABEL_Y);

      // Waveform
      ctx.beginPath();
      const N = Math.max(64, Math.floor((x1 - x0) / 2));
      for (let k = 0; k <= N; k++) {
        const p = k / N;
        const x = x0 + p * (x1 - x0);
        const y =
          Math.sin(2 * Math.PI * (3 * p + ts * 0.35)) * 0.5 +
          Math.sin(2 * Math.PI * (7 * p - ts * 0.6)) * 0.28 +
          Math.sin(2 * Math.PI * (13 * p + ts * 1.1)) * 0.12;
        const yy = WAVE_MID + y * WAVE_AMP;
        if (k === 0) ctx.moveTo(x, yy);
        else ctx.lineTo(x, yy);
      }
      ctx.strokeStyle = "#0E7C6B";
      ctx.lineWidth = 1.6;
      ctx.lineJoin = "round";
      ctx.stroke();

      // Waveform zero line + section divider
      ctx.strokeStyle = "#E7E0D3";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x0, WAVE_BASE);
      ctx.lineTo(x1, WAVE_BASE);
      ctx.moveTo(x0, DIVIDER_Y);
      ctx.lineTo(x1, DIVIDER_Y);
      ctx.stroke();

      // Frequency bars (bottom band only)
      const barAreaH = BAR_BASE - BAR_TOP;
      const bw = (x1 - x0) / BARS;
      for (let b = 0; b < BARS; b++) {
        const f =
          0.25 +
          0.55 * Math.abs(Math.sin(b * 0.55 + ts * 1.4)) *
            Math.exp(-b / 22) +
          0.12 * Math.abs(Math.sin(b * 1.7 - ts * 2.2));
        const bh = Math.max(3, Math.min(1, f) * barAreaH);
        const x = x0 + b * bw + bw * 0.18;
        ctx.fillStyle = b % 4 === 0 ? "#0E7C6B" : "#16A34A";
        ctx.globalAlpha = 0.85;
        const r = Math.min(3, bw * 0.3);
        ctx.beginPath();
        ctx.roundRect(x, BAR_BASE - bh, bw * 0.64, bh, r);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    function drawFile() {
      ctx.clearRect(0, 0, w, h);
      if (!waveform || waveform.length === 0) {
        ctx.fillStyle = "#6B7280";
        ctx.font = "12px 'IBM Plex Mono', monospace";
        ctx.fillText("No signal", PAD_X, 24);
        return;
      }
      const x0 = PAD_X;
      const x1 = w - PAD_X;
      const mid = h / 2;
      const amp = h / 2 - 16;
      ctx.beginPath();
      const N = waveform.length;
      for (let k = 0; k < N; k++) {
        const x = x0 + (k / (N - 1)) * (x1 - x0);
        const y = mid - waveform[k] * amp;
        if (k === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = "#0E7C6B";
      ctx.lineWidth = 1.4;
      ctx.lineJoin = "round";
      ctx.stroke();
      ctx.strokeStyle = "#E7E0D3";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x0, mid);
      ctx.lineTo(x1, mid);
      ctx.stroke();
    }

    function loop(t: number) {
      if (!running || document.hidden) {
        raf = requestAnimationFrame(loop);
        return;
      }
      if (mode === "file") drawFile();
      else drawDemo(t);
      if (!reduced) raf = requestAnimationFrame(loop);
    }

    if (reduced) {
      // Single static frame for reduced-motion users.
      if (mode === "file") drawFile();
      else drawDemo(1200);
    } else {
      raf = requestAnimationFrame(loop);
    }

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, waveform]);

  return (
    <div ref={wrapRef} className={`w-full min-w-0 overflow-hidden ${className}`}>
      <canvas ref={canvasRef} className="block w-full" aria-label="Live signal visualization" role="img" />
    </div>
  );
}
