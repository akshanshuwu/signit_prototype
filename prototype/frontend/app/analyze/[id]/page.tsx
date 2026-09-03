"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import SpectrumPlot from "../../../components/SpectrumPlot";
import WaterfallPlot from "../../../components/WaterfallPlot";
import ConstellationPlot from "../../../components/ConstellationPlot";
import ReportCard from "../../../components/ReportCard";
import MissionLog from "../../../components/MissionLog";
import Comparator from "../../../components/Comparator";
import BitsView from "../../../components/BitsView";
import { loadDemo, type DemoId, type DemoJson } from "../../../lib/demo";

const VALID: DemoId[] = ["bpsk", "qpsk", "qam16", "fsk2"];
type Tab = "report" | "spectrum" | "waterfall" | "constellation" | "compare" | "bits";
const TABS: Array<{ id: Tab; label: string }> = [
  { id: "report", label: "Report" },
  { id: "spectrum", label: "Spectrum" },
  { id: "waterfall", label: "Waterfall" },
  { id: "constellation", label: "Constellation" },
  { id: "compare", label: "Compare" },
  { id: "bits", label: "Bits" }
];

// Full tabbed results: report + spectrum + waterfall + constellation + compare + bits.
export default function ResultPage({ params }: { params: { id: string } }) {
  const id = params.id as DemoId;
  const [data, setData] = useState<DemoJson | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("report");

  useEffect(() => {
    if (!VALID.includes(id)) {
      setErr(`Unknown capture "${params.id}". Open one of bpsk / qpsk / qam16 / fsk2.`);
      return;
    }
    loadDemo(id).then(setData).catch((e) => setErr(e.message));
  }, [id, params.id]);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <Link href="/analyze" className="text-xs font-medium text-slate-500 hover:text-slate-300">← All captures</Link>
      <h1 className="mt-2 text-2xl font-bold text-slate-50">Analysis · {params.id.toUpperCase()}</h1>
      <p className="mt-1 text-xs text-slate-500">Automatic parameter estimation · spectrum, modulation, demodulation preview.</p>
      {err && <p className="mt-4 rounded border border-red-800 bg-red-950 p-3 text-sm text-red-200">{err}</p>}
      {!err && !data && <p className="mt-4 text-sm text-slate-400">Loading analysis…</p>}
      {data && (
        <div className="mt-4">
          <div className="flex flex-wrap gap-2">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
                  tab === t.id ? "bg-emerald-500 text-slate-950" : "border border-slate-700 text-slate-300 hover:border-slate-500 hover:bg-slate-900"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="mt-3 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            {tab === "report" && <ReportCard data={data} />}
            {tab === "spectrum" && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-300">Spectrum (PSD)</p>
                <SpectrumPlot freqs={data.psd.freqs} magsDb={data.psd.mags_db} />
              </div>
            )}
            {tab === "waterfall" && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-300">Waterfall (time-frequency)</p>
                <WaterfallPlot times={data.spectrogram.times} freqs={data.spectrogram.freqs} zDb={data.spectrogram.z_db} />
              </div>
            )}
            {tab === "constellation" && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-300">Constellation (I/Q)</p>
                <ConstellationPlot i={data.constellation.i} q={data.constellation.q} />
              </div>
            )}
            {tab === "compare" && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-300">.IQ vs .wav</p>
                <Comparator iqSnr={data.comparator.iq_snr} wavSnr={data.comparator.wav_snr} note={data.comparator.note} />
              </div>
            )}
            {tab === "bits" && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-300">Bits + correlation</p>
                <BitsView hex={data.bits_preview.hex} ascii={data.bits_preview.ascii} corrPeak={data.bits_preview.corr_peak} />
              </div>
            )}
          </div>
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <p className="mb-2 text-sm font-semibold text-slate-300">Processing log</p>
            <MissionLog lines={data.log} />
          </div>
        </div>
      )}
    </div>
  );
}
