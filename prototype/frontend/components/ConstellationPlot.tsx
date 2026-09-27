"use client";

import { useEffect, useRef } from "react";

interface Props {
  i: number[];
  q: number[];
}

export default function ConstellationPlot({ i, q }: Props) {
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
            x: i,
            y: q,
            type: "scattergl",
            mode: "markers",
            marker: { color: "#0E7C6B", size: 2.5, opacity: 0.65 }
          }
        ],
        {
          margin: { l: 48, r: 12, t: 12, b: 40 },
          xaxis: { title: "I", color: "#6B7280", gridcolor: "#E7E0D3", zerolinecolor: "#D9D0BE" },
          yaxis: {
            title: "Q",
            color: "#6B7280",
            gridcolor: "#E7E0D3",
            zerolinecolor: "#D9D0BE",
            scaleanchor: "x",
            scaleratio: 1
          },
          paper_bgcolor: "#FFFFFF",
          plot_bgcolor: "#FFFFFF",
          font: { color: "#6B7280", size: 10, family: "IBM Plex Mono, monospace" }
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
  }, [i, q]);

  return <div ref={divRef} className="h-64 w-full min-w-0 overflow-hidden rounded-md border border-line bg-white sm:h-72" />;
}
