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
        [{ x: freqKhz, y: magsDb, type: "scatter", mode: "lines", line: { color: "#3DDC84", width: 1.5 } }],
        {
          margin: { l: 48, r: 12, t: 12, b: 40 },
          xaxis: { title: "Freq (kHz)", color: "#8B98A9", gridcolor: "#1C2536" },
          yaxis: { title: "Mag (dB)", color: "#8B98A9", gridcolor: "#1C2536" },
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
  }, [freqs, magsDb]);

  return <div ref={divRef} className="h-72 w-full border border-line" />;
}
