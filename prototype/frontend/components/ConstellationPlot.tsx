"use client";

import { useEffect, useRef } from "react";

interface Props {
  i: number[];
  q: number[];
}

export default function ConstellationPlot({ i, q }: Props) {
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
            x: i,
            y: q,
            type: "scattergl",
            mode: "markers",
            marker: { color: "#22d3ee", size: 3, opacity: 0.6 }
          }
        ],
        {
          margin: { l: 48, r: 12, t: 12, b: 40 },
          xaxis: { title: "I", color: "#94a3b8", gridcolor: "#1e293b", zerolinecolor: "#334155" },
          yaxis: {
            title: "Q",
            color: "#94a3b8",
            gridcolor: "#1e293b",
            zerolinecolor: "#334155",
            scaleanchor: "x",
            scaleratio: 1
          },
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
  }, [i, q]);

  return <div ref={divRef} className="h-64 w-full" />;
}
