"use client";

import { useEffect, useRef } from "react";

interface CorrPeak {
  lag: number;
  value: number;
  lags: number[];
  vals: number[];
}

interface Props {
  hex: string;
  ascii: string;
  corrPeak: CorrPeak;
}

export default function BitsView({ hex, ascii, corrPeak }: Props) {
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
        [{ x: corrPeak.lags, y: corrPeak.vals, type: "scatter", mode: "lines", line: { color: "#1A1E22", width: 1.5 } }],
        {
          margin: { l: 40, r: 12, t: 12, b: 40 },
          xaxis: { title: "Lag", color: "#6B7280", gridcolor: "#E7E0D3" },
          yaxis: { title: "Corr", color: "#6B7280", gridcolor: "#E7E0D3" },
          paper_bgcolor: "#FFFFFF",
          plot_bgcolor: "#FFFFFF",
          font: { color: "#6B7280", size: 10, family: "IBM Plex Mono, monospace" },
          shapes: [
            { type: "line", x0: corrPeak.lag, x1: corrPeak.lag, y0: 0, y1: 1, yref: "paper", line: { color: "#16A34A", width: 1, dash: "dash" } }
          ]
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
  }, [corrPeak]);

  return (
    <div className="min-w-0 space-y-3">
      <div className="grid min-w-0 grid-cols-1 gap-px border border-line bg-line md:grid-cols-2">
        <div className="min-w-0 bg-panel p-2.5">
          <p className="font-mono text-[11px] text-fog">HEX · FIRST 32B</p>
          <pre className="mt-1 max-h-28 min-w-0 overflow-auto break-all rounded-md bg-console p-2 font-mono text-[12px] text-paper">{hex}</pre>
        </div>
        <div className="min-w-0 bg-panel p-2.5">
          <p className="font-mono text-[11px] text-fog">ASCII</p>
          <pre className="mt-1 max-h-28 min-w-0 overflow-auto break-all rounded-md bg-console p-2 font-mono text-[12px] text-paper">{ascii}</pre>
        </div>
      </div>
      <div className="min-w-0">
        <p className="font-mono text-[11px] text-fog">SYNC PEAK · LAG {corrPeak.lag} · VAL {corrPeak.value.toFixed(2)}</p>
        <div ref={divRef} className="mt-1 h-48 w-full min-w-0 overflow-hidden rounded-md border border-line bg-white" />
      </div>
    </div>
  );
}
