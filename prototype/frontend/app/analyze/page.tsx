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
import DownloadExe from "../../components/DownloadExe";
import type { DemoJson } from "../../lib/analysis";

type Tab = "report" | "spectrum" | "waterfall" | "constellation" | "compare" | "bits";
const TABS: Array<{ id: Tab; label: string }> = [
  { id: "report", label: "REPORT" },
  { id: "spectrum", label: "SPECTRUM" },
  { id: "waterfall", label: "WATERFALL" },
  { id: "constellation", label: "CONSTELLATION" },
  { id: "compare", label: "COMPARE" },
  { id: "bits", label: "BITS" }
];

export default function AnalyzePage() {
  const [data, setData] = useState<DemoJson | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("report");
  const [ms, setMs] = useState<number | null>(null);

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <Link href="/" className="font-mono text-[12px] text-fog hover:text-paper">← INDEX</Link>
      <div className="mt-2 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-4">
        <div>
          <p className="kicker">01 // Analyzer</p>
          <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">Triage a capture</h1>
        </div>
        <p className="font-mono text-[11px] text-fog">.iq / .wav / .bin · ≤100 MB · head preview &gt;15 MB · zero upload</p>
      </div>

      <div className="mt-5">
        <UploadBox
          onResult={(d, took) => { setData(d); setMs(took); setErr(null); setTab("report"); }}
          onError={(m) => setErr(m)}
        />
      </div>

      {err && !data && (
        <p className="mt-4 border border-warn/60 bg-warn/10 p-3 font-mono text-[12px] text-warn">{err}</p>
      )}

      {!data && !err && (
        <div className="mt-5 grid gap-px border border-line bg-line md:grid-cols-3">
          {[
            ["1 — SET FORMAT", ".iq needs sampling rate + int16 / float32 / uint8. .wav self-describes."],
            ["2 — DROP FILE", "1–5 MB .wav answers instantly. Large files read a 262144-sample head."],
            ["3 — READ VERDICT", "Report first. Then FIG.01 → FIG.02 → FIG.03 → bits."]
          ].map(([t, d]) => (
            <div key={t} className="bg-panel p-4">
              <p className="font-mono text-[12px] font-bold text-paper">{t}</p>
              <p className="mt-1 text-[12px] leading-relaxed text-fog">{d}</p>
            </div>
          ))}
        </div>
      )}

      {data && (
        <div className="mt-6">
          <div className="console-frame">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line bg-console px-4 py-2.5 font-mono text-[12px]">
              <p className="truncate">FILE <span className="text-paper">{data.meta.file}</span></p>
              <p className="text-fog">MOD <span className="text-signal">{data.predictions.modulation}</span> · CONF {(data.predictions.confidence * 100).toFixed(0)}%{ms !== null && <> · {ms} MS ON-DEVICE</>}</p>
            </div>
            <div className="flex gap-0 overflow-x-auto border-b border-line font-mono text-[12px]">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`border-b-2 px-4 py-2.5 font-bold tracking-wide ${
                    tab === t.id
                      ? "border-signal bg-console text-paper"
                      : "border-transparent text-fog hover:text-paper"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <div className="grid gap-px bg-line lg:grid-cols-5">
              <div className="bg-panel p-5 lg:col-span-3">
                {tab === "report" && <ReportCard data={data} />}
                {tab === "spectrum" && (
                  <div>
                    <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.01 — SPECTRUM · kHz / dB</p>
                    <SpectrumPlot freqs={data.psd.freqs} magsDb={data.psd.mags_db} />
                  </div>
                )}
                {tab === "waterfall" && (
                  <div>
                    <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.02 — WATERFALL · time × freq</p>
                    <WaterfallPlot times={data.spectrogram.times} freqs={data.spectrogram.freqs} zDb={data.spectrogram.z_db} />
                  </div>
                )}
                {tab === "constellation" && (
                  <div>
                    <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.03 — CONSTELLATION · I/Q</p>
                    <ConstellationPlot i={data.constellation.i} q={data.constellation.q} />
                  </div>
                )}
                {tab === "compare" && (
                  <div>
                    <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.04 — .IQ VS .WAV · dB</p>
                    <Comparator iqSnr={data.comparator.iq_snr} wavSnr={data.comparator.wav_snr} note={data.comparator.note} />
                  </div>
                )}
                {tab === "bits" && (
                  <div>
                    <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.05 — BITS + SYNC</p>
                    <BitsView hex={data.bits_preview.hex} ascii={data.bits_preview.ascii} corrPeak={data.bits_preview.corr_peak} />
                  </div>
                )}
              </div>
              <div className="space-y-px bg-line lg:col-span-2">
                <div className="bg-panel p-4">
                  <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">MISSION LOG</p>
                  <MissionLog lines={data.log} />
                </div>
                <div className="bg-panel p-4">
                  <DownloadExe compact />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-10">
        <DownloadExe />
      </div>
    </div>
  );
}
