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

  useEffect(() => {
    let cancelled = false;
    async function draw() {
      if (!divRef.current) return;
      const Plotly = (await import("plotly.js-dist-min")).default;
      if (cancelled) return;
      await Plotly.react(
        divRef.current,
        [{ x: corrPeak.lags, y: corrPeak.vals, type: "scatter", mode: "lines", line: { color: "#a78bfa", width: 1.5 } }],
        {
          margin: { l: 40, r: 12, t: 12, b: 40 },
          xaxis: { title: "Lag", color: "#94a3b8", gridcolor: "#1e293b" },
          yaxis: { title: "Corr", color: "#94a3b8", gridcolor: "#1e293b" },
          paper_bgcolor: "#020617",
          plot_bgcolor: "#020617",
          font: { color: "#94a3b8", size: 11 },
          shapes: [
            { type: "line", x0: corrPeak.lag, x1: corrPeak.lag, y0: 0, y1: 1, yref: "paper", line: { color: "#f59e0b", width: 1, dash: "dash" } }
          ]
        },
        { responsive: true, displayModeBar: false }
      );
    }
    draw();
    return () => {
      cancelled = true;
    };
  }, [corrPeak]);

  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <p className="text-xs text-slate-500">Hex (first 32 bytes)</p>
          <pre className="mt-1 max-h-28 overflow-auto rounded bg-black/40 p-2 font-mono text-xs text-green-300">{hex}</pre>
        </div>
        <div>
          <p className="text-xs text-slate-500">ASCII preview</p>
          <pre className="mt-1 max-h-28 overflow-auto rounded bg-black/40 p-2 font-mono text-xs text-green-300">{ascii}</pre>
        </div>
      </div>
      <div>
        <p className="text-xs text-slate-500">Sync correlation peak: lag {corrPeak.lag}, value {corrPeak.value.toFixed(2)}</p>
        <div ref={divRef} className="mt-1 h-48 w-full" />
      </div>
    </div>
  );
}
