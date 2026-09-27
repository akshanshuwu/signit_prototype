"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import UploadBox from "../../components/UploadBox";
import SpectrumPlot from "../../components/SpectrumPlot";
import WaterfallPlot from "../../components/WaterfallPlot";
import ConstellationPlot from "../../components/ConstellationPlot";
import ReportCard from "../../components/ReportCard";
import MissionLog from "../../components/MissionLog";
import Comparator from "../../components/Comparator";
import BitsView from "../../components/BitsView";
import DownloadExe from "../../components/DownloadExe";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import AudioPlayer from "../../components/AudioPlayer";
import WaveformPlayhead from "../../components/WaveformPlayhead";
import LiveSpectrumCanvas from "../../components/LiveSpectrumCanvas";
import ConstellationLiveCanvas from "../../components/ConstellationLiveCanvas";
import { usePlaybackSync } from "../../hooks/usePlaybackSync";
import { usePlaybackCursor } from "../../hooks/usePlaybackCursor";
import { computePeaks, toPlaybackMono, type PlaybackData } from "../../lib/dsp/playback";
import type { IQData } from "../../lib/dsp/parse";
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
  const [iq, setIq] = useState<IQData | null>(null);

  const playback: PlaybackData | null = useMemo(
    () => (iq ? toPlaybackMono(iq) : null),
    [iq]
  );
  const sync = usePlaybackSync(playback);
  const peaks = useMemo(
    () => (playback ? computePeaks(playback.mono) : null),
    [playback]
  );
  const isPlaying = sync.status === "playing";
  // Waterfall cursor sampled ~10Hz, only while its tab is visible.
  const waterfallCursor = usePlaybackCursor(
    sync.getTime,
    isPlaying,
    tab === "waterfall" && data !== null
  );

  return (
    <div className="mx-auto min-w-0 max-w-6xl px-4 py-6 sm:px-6 sm:py-10">
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
          onResult={(d, took, decoded) => { setData(d); setMs(took); setIq(decoded); setErr(null); setTab("report"); }}
          onError={(m) => setErr(m)}
        />
      </div>

      {data && iq && playback && peaks && (
        <div className="signit-enter mt-5 space-y-3">
          <AudioPlayer sync={sync} fileName={iq.fileName} sonified={playback.sonified} />
          <div>
            <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">
              WAVEFORM · CLICK / DRAG TO SEEK · {sync.duration.toFixed(1)}S PREVIEW
            </p>
            <WaveformPlayhead
              peaks={peaks}
              duration={sync.duration}
              getTime={sync.getTime}
              playing={sync.status === "playing"}
              onSeek={sync.seek}
            />
          </div>
        </div>
      )}

      {err && !data && (
        <div className="signit-card mt-4 border-warn/60 bg-warn/10 p-4" role="alert">
          <p className="font-mono text-[12px] font-bold text-warn">Couldn&apos;t analyze that file</p>
          <p className="mt-1 break-words font-mono text-[12px] text-paper">{err}</p>
          <p className="mt-2 text-[12px] leading-relaxed text-fog">
            Check the format and try again — .wav should be PCM16/32F, .iq/.bin needs the
            matching sampling rate + int16 / float32 / uint8 layout.
          </p>
        </div>
      )}

      {!data && !err && (
        <div className="mt-5 space-y-4">
          <EmptyState
            title="Drop a capture to begin"
            body=".iq / .wav / .bin up to 100 MB · analyzed 100% in-browser, nothing is uploaded. 1–5 MB .wav answers instantly; larger files read a 262144-sample head preview."
          />
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["1 — SET FORMAT", ".iq needs sampling rate + int16 / float32 / uint8. .wav self-describes."],
              ["2 — DROP FILE", "1–5 MB .wav answers instantly. Large files read a 262144-sample head."],
              ["3 — READ VERDICT", "Report first. Then FIG.01 → FIG.02 → FIG.03 → bits."]
            ].map(([t, d]) => (
              <Card key={t} className="p-4">
                <p className="font-mono text-[12px] font-bold text-paper">{t}</p>
                <p className="mt-1 text-[12px] leading-relaxed text-fog">{d}</p>
              </Card>
            ))}
          </div>
        </div>
      )}

      {data && (
        <div className="mt-6 min-w-0">
          <div className="console-frame min-w-0 overflow-hidden">
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 border-b border-line bg-console px-4 py-2.5 font-mono text-[12px]">
              <p className="min-w-0 flex-1 truncate">FILE <span className="text-paper">{data.meta.file}</span></p>
              <p className="shrink-0 text-fog">MOD <span className="text-signal">{data.predictions.modulation}</span> · CONF {(data.predictions.confidence * 100).toFixed(0)}%{ms !== null && <> · {ms} MS ON-DEVICE</>}</p>
            </div>
            <div className="flex min-w-0 gap-0 overflow-x-auto border-b border-line font-mono text-[12px]" role="tablist" aria-label="Analysis views">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  role="tab"
                  aria-selected={tab === t.id}
                  onClick={() => setTab(t.id)}
                  className={`shrink-0 border-b-2 px-4 py-2.5 font-bold tracking-wide ${
                    tab === t.id
                      ? "border-signal bg-console text-paper"
                      : "border-transparent text-fog hover:text-paper"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <div className="grid min-w-0 grid-cols-1 gap-px bg-line lg:grid-cols-[minmax(0,1fr)_320px]">
              <div className="min-w-0 bg-panel p-4 sm:p-5">
                {tab === "report" && <ReportCard data={data} />}
                {tab === "spectrum" && (
                  <div className="min-w-0 space-y-4">
                    {iq && (
                      <div>
                        <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">LIVE — OUTPUT SPECTRUM · follows playback</p>
                        <LiveSpectrumCanvas analyserRef={sync.analyserRef} playing={isPlaying} />
                      </div>
                    )}
                    <div>
                      <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.01 — SPECTRUM · kHz / dB · full capture</p>
                      <SpectrumPlot freqs={data.psd.freqs} magsDb={data.psd.mags_db} />
                    </div>
                  </div>
                )}
                {tab === "waterfall" && (
                  <div className="min-w-0">
                    <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.02 — WATERFALL · time × freq{waterfallCursor !== null ? " · cursor follows playback" : ""}</p>
                    <WaterfallPlot times={data.spectrogram.times} freqs={data.spectrogram.freqs} zDb={data.spectrogram.z_db} cursorTime={waterfallCursor} />
                  </div>
                )}
                {tab === "constellation" && (
                  <div className="min-w-0 space-y-4">
                    {iq && (
                      <div>
                        <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">LIVE — 512-SYMBOL WINDOW · follows playback{iq.kind === "wav" ? " · I-only (mono wav)" : ""}</p>
                        <ConstellationLiveCanvas i={iq.i} q={iq.q} fs={iq.fs} getTime={sync.getTime} playing={isPlaying} />
                      </div>
                    )}
                    <div>
                      <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.03 — CONSTELLATION · I/Q · full capture</p>
                      <ConstellationPlot i={data.constellation.i} q={data.constellation.q} />
                    </div>
                  </div>
                )}
                {tab === "compare" && (
                  <div className="min-w-0">
                    <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.04 — .IQ VS .WAV · dB</p>
                    <Comparator iqSnr={data.comparator.iq_snr} wavSnr={data.comparator.wav_snr} note={data.comparator.note} />
                  </div>
                )}
                {tab === "bits" && (
                  <div className="min-w-0">
                    <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">FIG.05 — BITS + SYNC</p>
                    <BitsView hex={data.bits_preview.hex} ascii={data.bits_preview.ascii} corrPeak={data.bits_preview.corr_peak} />
                  </div>
                )}
              </div>
              <div className="min-w-0 space-y-px bg-line">
                <div className="min-w-0 bg-panel p-4">
                  <p className="mb-2 font-mono text-[11px] tracking-[0.18em] text-fog">MISSION LOG</p>
                  <MissionLog lines={data.log} />
                </div>
                <div className="min-w-0 bg-panel p-4">
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
