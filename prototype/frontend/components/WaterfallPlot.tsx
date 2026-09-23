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
            colorbar: { title: "dB", tickfont: { color: "#8B98A9" } }
          }
        ],
        {
          margin: { l: 48, r: 60, t: 12, b: 40 },
          xaxis: { title: "Time (s)", color: "#8B98A9", gridcolor: "#1C2536" },
          yaxis: { title: "Freq (kHz)", color: "#8B98A9", gridcolor: "#1C2536" },
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
  }, [times, freqs, zDb]);

  return <div ref={divRef} className="h-72 w-full border border-line" />;
}
