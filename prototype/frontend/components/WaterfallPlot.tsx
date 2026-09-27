"use client";

import { useEffect, useRef } from "react";

interface Props {
  times: number[];
  freqs: number[];
  zDb: number[][];
  /** Playback cursor in seconds (sampled ~10Hz by parent). Null hides it. */
  cursorTime?: number | null;
}

function cursorShape(t: number) {
  return {
    type: "line",
    x0: t,
    x1: t,
    y0: 0,
    y1: 1,
    yref: "paper",
    line: { color: "#0E7C6B", width: 2, dash: "dash" },
  };
}

export default function WaterfallPlot({ times, freqs, zDb, cursorTime = null }: Props) {
  const divRef = useRef<HTMLDivElement>(null);
  const plotlyRef = useRef<any>(null);

  // Resize with the container (window resize, sidebar collapse, breakpoints).
  useEffect(() => {
    const el = divRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      const P = plotlyRef.current;
      if (P && el) P.Plots.resize(el).catch(() => {});
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function draw() {
      if (!divRef.current) return;
      const Plotly = (await import("plotly.js-dist-min")).default;
      if (cancelled) return;
      plotlyRef.current = Plotly;
      await Plotly.react(
        divRef.current,
        [
          {
            x: times,
            y: freqs.map((f) => f / 1000),
            z: zDb,
            type: "heatmap",
            colorscale: "Viridis",
            showscale: true,
            colorbar: { title: "dB", tickfont: { color: "#6B7280" } }
          }
        ],
        {
          margin: { l: 48, r: 60, t: 12, b: 40 },
          xaxis: { title: "Time (s)", color: "#6B7280", gridcolor: "#E7E0D3" },
          yaxis: { title: "Freq (kHz)", color: "#6B7280", gridcolor: "#E7E0D3" },
          paper_bgcolor: "#FFFFFF",
          plot_bgcolor: "#FFFFFF",
          font: { color: "#6B7280", size: 10, family: "IBM Plex Mono, monospace" },
          shapes: cursorTime !== null ? [cursorShape(cursorTime)] : []
        },
        { responsive: true, displayModeBar: false }
      );
    }
    draw();
    return () => {
      cancelled = true;
      plotlyRef.current = null;
      if (divRef.current) {
        import("plotly.js-dist-min").then((m) => (m.default as any).purge(divRef.current!)).catch(() => {});
      }
    };
  }, [times, freqs, zDb]);

  // Live cursor overlay — relayout only, never a full redraw.
  const cursorRef = useRef<number | null>(null);
  useEffect(() => {
    cursorRef.current = cursorTime;
    const Plotly = plotlyRef.current;
    if (!Plotly || !divRef.current) return;
    Plotly.relayout(divRef.current, {
      shapes: cursorTime !== null ? [cursorShape(cursorTime)] : [],
    }).catch(() => {});
  }, [cursorTime]);

  return <div ref={divRef} className="h-64 w-full min-w-0 overflow-hidden rounded-md border border-line bg-white sm:h-72" />;
}
