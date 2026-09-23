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
            marker: { color: "#3DDC84", size: 2.5, opacity: 0.65 }
          }
        ],
        {
          margin: { l: 48, r: 12, t: 12, b: 40 },
          xaxis: { title: "I", color: "#8B98A9", gridcolor: "#1C2536", zerolinecolor: "#2A3648" },
          yaxis: {
            title: "Q",
            color: "#8B98A9",
            gridcolor: "#1C2536",
            zerolinecolor: "#2A3648",
            scaleanchor: "x",
            scaleratio: 1
          },
          paper_bgcolor: "#0A0F1A",
          plot_bgcolor: "#0A0F1A",
          font: { color: "#8B98A9", size: 10, family: "IBM Plex Mono, monospace" }
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
  }, [i, q]);

  return <div ref={divRef} className="h-72 w-full border border-line" />;
}
