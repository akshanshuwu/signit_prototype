"use client";

import { useEffect, useRef } from "react";

interface Props {
  times: number[];
  freqs: number[];
  zDb: number[][];
}

export default function WaterfallPlot({ times, freqs, zDb }: Props) {
  const divRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function draw() {
      if (!divRef.current) return;
      const Plotly = (await import("plotly.js-dist-min")).default;
      if (cancelled) return;
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
            colorbar: { title: "dB", tickfont: { color: "#94a3b8" } }
          }
        ],
        {
          margin: { l: 48, r: 60, t: 12, b: 40 },
          xaxis: { title: "Time (s)", color: "#94a3b8", gridcolor: "#1e293b" },
          yaxis: { title: "Freq (kHz)", color: "#94a3b8", gridcolor: "#1e293b" },
          paper_bgcolor: "#020617",
          plot_bgcolor: "#020617",
          font: { color: "#94a3b8", size: 11 }
        },
        { responsive: true, displayModeBar: false }
      );
    }
    draw();
    return () => {
      cancelled = true;
    };
  }, [times, freqs, zDb]);

  return <div ref={divRef} className="h-64 w-full" />;
}
