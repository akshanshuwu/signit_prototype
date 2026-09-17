"use client";

import Link from "next/link";
import { useState } from "react";
import UploadBox from "../../components/UploadBox";
import SpectrumPlot from "../../components/SpectrumPlot";
import WaterfallPlot from "../../components/WaterfallPlot";
import ConstellationPlot from "../../components/ConstellationPlot";
import ReportCard from "../../components/ReportCard";
import MissionLog from "../../components/MissionLog";
import Comparator from "../../components/Comparator";
import BitsView from "../../components/BitsView";
import type { DemoJson } from "../../lib/analysis";

type Tab = "report" | "spectrum" | "waterfall" | "constellation" | "compare" | "bits";
const TABS: Array<{ id: Tab; label: string }> = [
  { id: "report", label: "Report" },
  { id: "spectrum", label: "Spectrum" },
  { id: "waterfall", label: "Waterfall" },
  { id: "constellation", label: "Constellation" },
  { id: "compare", label: "Compare" },
  { id: "bits", label: "Bits" }
];

export default function AnalyzePage() {
  const [data, setData] = useState<DemoJson | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("report");

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Link href="/" className="text-xs font-medium text-slate-500 hover:text-slate-300">← Home</Link>
      <h1 className="mt-2 text-2xl font-bold text-slate-50">Analyze a capture</h1>
      <p className="mt-1 text-sm text-slate-400">Drop an .iq, .wav or .bin recording for full spectrum, modulation and bit-stream analysis.</p>
      <div className="mt-6">
        <UploadBox
          onResult={(d) => { setData(d); setErr(null); }}
          onError={(m) => setErr(m)}
        />
      </div>
      {err && !data && <p className="mt-4 rounded border border-red-800 bg-red-950 p-3 text-sm text-red-200">{err}</p>}
      {data && (
        <div className="mt-8">
          <h2 className="text-sm font-semibold text-slate-200">Analysis · {data.meta.file}</h2>
          <div className="mt-3 flex flex-wrap gap-2">
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
