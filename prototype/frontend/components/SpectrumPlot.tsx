"use client";

import { useEffect, useRef } from "react";

interface Props {
  freqs: number[];
  magsDb: number[];
}

export default function SpectrumPlot({ freqs, magsDb }: Props) {
  const divRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function draw() {
      if (!divRef.current) return;
      const Plotly = (await import("plotly.js-dist-min")).default;
      if (cancelled) return;
      const freqKhz = freqs.map((f) => f / 1000);
      await Plotly.react(
        divRef.current,
        [{ x: freqKhz, y: magsDb, type: "scatter", mode: "lines", line: { color: "#22d3ee", width: 1.5 } }],
        {
          margin: { l: 48, r: 12, t: 12, b: 40 },
          xaxis: { title: "Freq (kHz)", color: "#94a3b8", gridcolor: "#1e293b" },
          yaxis: { title: "Mag (dB)", color: "#94a3b8", gridcolor: "#1e293b" },
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
  }, [freqs, magsDb]);

  return <div ref={divRef} className="h-64 w-full" />;
}
