"use client";

// Offscreen Plotly export: re-renders the ACTUAL current DemoJson figures
// into hidden divs and captures them as PNG data URLs for the PDF report.
// Works regardless of which tab is visible (mounted plots are tab-gated).

import type { DemoJson } from "./analysis";

const FONT = "IBM Plex Mono, monospace";
const W = 1000;
const H = 520;

async function renderToPng(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  trace: any,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  layoutExtra: any
): Promise<string | null> {
  try {
    const mod = await import("plotly.js-dist-min");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const Plotly = (mod as any).default ?? mod;
    const div = document.createElement("div");
    div.style.position = "fixed";
    div.style.left = "-10000px";
    div.style.top = "0";
    div.style.width = `${W}px`;
    div.style.height = `${H}px`;
    document.body.appendChild(div);
    try {
      await Plotly.newPlot(
        div,
        [trace],
        {
          margin: { l: 60, r: 20, t: 20, b: 56 },
          paper_bgcolor: "#FFFFFF",
          plot_bgcolor: "#FFFFFF",
          font: { color: "#1A1E22", size: 11, family: FONT },
          ...layoutExtra,
        },
        { staticPlot: true, displayModeBar: false }
      );
      const url = (await Plotly.toImage(div, {
        format: "png",
        width: W,
        height: H,
      })) as string;
      return url;
    } finally {
      try {
        await Plotly.purge(div);
      } catch {
        /* noop */
      }
      div.remove();
    }
  } catch {
    return null;
  }
}

function axis(title: string) {
  return { title, color: "#6B7280", gridcolor: "#E7E0D3" };
}

export async function spectrumPng(d: DemoJson): Promise<string | null> {
  return renderToPng(
    {
      x: d.psd.freqs.map((f) => f / 1000),
      y: d.psd.mags_db,
      type: "scatter",
      mode: "lines",
      line: { color: "#16A34A", width: 1.5 },
    },
    { xaxis: axis("Freq (kHz)"), yaxis: axis("Mag (dB)") }
  );
}

export async function waterfallPng(d: DemoJson): Promise<string | null> {
  return renderToPng(
    {
      x: d.spectrogram.times,
      y: d.spectrogram.freqs.map((f) => f / 1000),
      z: d.spectrogram.z_db,
      type: "heatmap",
      colorscale: "Viridis",
      showscale: true,
    },
    { xaxis: axis("Time (s)"), yaxis: axis("Freq (kHz)") }
  );
}

export async function constellationPng(d: DemoJson): Promise<string | null> {
  return renderToPng(
    {
      x: d.constellation.i,
      y: d.constellation.q,
      type: "scattergl",
      mode: "markers",
      marker: { color: "#0E7C6B", size: 3, opacity: 0.65 },
    },
    {
      xaxis: { ...axis("I"), zerolinecolor: "#D9D0BE" },
      yaxis: {
        ...axis("Q"),
        zerolinecolor: "#D9D0BE",
        scaleanchor: "x",
        scaleratio: 1,
      },
    }
  );
}

export async function corrPng(d: DemoJson): Promise<string | null> {
  const c = d.bits_preview.corr_peak;
  return renderToPng(
    {
      x: c.lags,
      y: c.vals,
      type: "scatter",
      mode: "lines",
      line: { color: "#1A1E22", width: 1.5 },
    },
    {
      xaxis: axis("Lag"),
      yaxis: axis("Corr"),
      shapes: [
        {
          type: "line",
          x0: c.lag,
          x1: c.lag,
          y0: 0,
          y1: 1,
          yref: "paper",
          line: { color: "#16A34A", width: 1.5, dash: "dash" },
        },
      ],
    }
  );
}

/** Waveform overview PNG drawn from real playback mono (RMS peaks). */
export function waveformPng(mono: Float32Array | null, bins = 1000): string | null {
  try {
    if (!mono || mono.length === 0) return null;
    const Wpx = 1000;
    const Hpx = 260;
    const canvas = document.createElement("canvas");
    canvas.width = Wpx;
    canvas.height = Hpx;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, Wpx, Hpx);
    const mid = Hpx / 2;
    const n = Math.min(bins, mono.length);
    const per = mono.length / n;
    let peak = 0;
    const vals = new Float32Array(n);
    for (let b = 0; b < n; b++) {
      const s = Math.floor(b * per);
      const e = Math.max(s + 1, Math.floor((b + 1) * per));
      let sum = 0;
      for (let k = s; k < e && k < mono.length; k++) sum += mono[k] * mono[k];
      vals[b] = Math.sqrt(sum / (e - s));
      if (vals[b] > peak) peak = vals[b];
    }
    const g = peak > 1e-9 ? (Hpx / 2 - 16) / peak : 1;
    ctx.fillStyle = "#0E7C6B";
    const bw = Wpx / n;
    for (let b = 0; b < n; b++) {
      const bh = Math.max(1, vals[b] * g);
      ctx.fillRect(b * bw, mid - bh, Math.max(1, bw * 0.8), bh * 2);
    }
    ctx.strokeStyle = "#E7E0D3";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, mid);
    ctx.lineTo(Wpx, mid);
    ctx.stroke();
    return canvas.toDataURL("image/png");
  } catch {
    return null;
  }
}
