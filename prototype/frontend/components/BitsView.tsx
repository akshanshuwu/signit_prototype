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
        [{ x: corrPeak.lags, y: corrPeak.vals, type: "scatter", mode: "lines", line: { color: "#E6EDF3", width: 1.5 } }],
        {
          margin: { l: 40, r: 12, t: 12, b: 40 },
          xaxis: { title: "Lag", color: "#8B98A9", gridcolor: "#1C2536" },
          yaxis: { title: "Corr", color: "#8B98A9", gridcolor: "#1C2536" },
          paper_bgcolor: "#0A0F1A",
          plot_bgcolor: "#0A0F1A",
          font: { color: "#8B98A9", size: 10, family: "IBM Plex Mono, monospace" },
          shapes: [
            { type: "line", x0: corrPeak.lag, x1: corrPeak.lag, y0: 0, y1: 1, yref: "paper", line: { color: "#3DDC84", width: 1, dash: "dash" } }
          ]
        },
        { responsive: true, displayModeBar: false }
      );
    }
    draw();
    return () => {
      cancelled = true;
      if (divRef.current) {
        import("plotly.js-dist-min").then((m) => (m.default as any).purge(divRef.current!)).catch(() => {});
      }
    };
  }, [corrPeak]);

  return (
    <div className="space-y-3">
      <div className="grid gap-px border border-line bg-line md:grid-cols-2">
        <div className="bg-panel p-2.5">
          <p className="font-mono text-[11px] text-fog">HEX · FIRST 32B</p>
          <pre className="mt-1 max-h-28 overflow-auto bg-console p-2 font-mono text-[12px] text-paper">{hex}</pre>
        </div>
        <div className="bg-panel p-2.5">
          <p className="font-mono text-[11px] text-fog">ASCII</p>
          <pre className="mt-1 max-h-28 overflow-auto bg-console p-2 font-mono text-[12px] text-paper">{ascii}</pre>
        </div>
      </div>
      <div>
        <p className="font-mono text-[11px] text-fog">SYNC PEAK · LAG {corrPeak.lag} · VAL {corrPeak.value.toFixed(2)}</p>
        <div ref={divRef} className="mt-1 h-48 w-full border border-line" />
      </div>
    </div>
  );
}
