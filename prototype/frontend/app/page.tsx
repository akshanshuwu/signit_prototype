import Link from "next/link";
import DownloadExe from "../components/DownloadExe";
import Card from "../components/ui/Card";
import SectionTitle from "../components/ui/SectionTitle";
import LiveHeroViz from "../components/LiveHeroViz";

const PIPELINE = [
  { n: "01", t: "INGEST", d: "memmap read · int16 / float32 / uint8 IQ or PCM wav · SHA logged · ≤100 MB, head preview over 15 MB." },
  { n: "02", t: "MEASURE", d: "Welch PSD 512pt · STFT 128×64 · SNR / BW / symbol-rate estimators · ≤2000 constellation symbols." },
  { n: "03", t: "DECIDE", d: "Cumulant classifier over BPSK / QPSK / 16QAM / 2FSK with confidence 0–100. UNKNOWN when undecidable." },
  { n: "04", t: "DECODE", d: "Demod preview · 32-byte hex + ASCII · sync correlation peak (lag / value)." }
];

const SPECS = [
  ["INPUT", ".iq / .wav / .bin · int16 IQ default · fs 48k / 96k / 192k / 1M"],
  ["ENGINE", "Welch + STFT + estimators · in-browser · zero upload"],
  ["OUTPUT", "FIG.01 spectrum · FIG.02 waterfall · FIG.03 constellation · bits + log"]
];

export default function LandingPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
      <div className="grid min-w-0 gap-6 pt-8 sm:pt-12 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <p className="kicker">SIGNIT // RF capture analyzer</p>
          <h1 className="mt-4 font-display text-4xl font-bold leading-[1.02] tracking-tight sm:text-6xl">
            Read the capture.<br />Name the signal.
          </h1>
          <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-fog">
            Drop an off-air recording. SIGNIT measures sampling rate, bandwidth, carrier offset and SNR,
            votes a modulation with confidence, and lays out spectrum, waterfall, constellation and bits
            for inspection. Field path: web triage here, full offline proof in the Windows build.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/analyze" className="btn-primary px-5 py-2.5 font-mono text-[13px]">
              OPEN ANALYZER
            </Link>
            <Link href="#download" className="btn-secondary px-5 py-2.5 font-mono text-[13px]">
              WINDOWS BUILD
            </Link>
          </div>
          <dl className="mt-8 divide-y divide-line border-y border-line font-mono text-[12px]">
            {SPECS.map(([k, v]) => (
              <div key={k} className="grid grid-cols-[88px_1fr] gap-3 py-2.5">
                <dt className="text-signal">{k}</dt>
                <dd className="text-fog">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
        <aside className="min-w-0 lg:col-span-4">
          <Card>
            <SectionTitle kicker="Live" title="Signal preview" hint="DEMO" />
            <div className="mt-3 overflow-hidden rounded-md border border-line">
              <LiveHeroViz mode="demo" />
            </div>
            <p className="mt-3 text-[12px] leading-relaxed text-fog">
              Waveform + spectrum preview of what SIGNIT measures. Upload a
              capture in the Analyzer to see your real signal here.
            </p>
            <Link href="/analyze" className="btn-secondary mt-4 block px-3 py-2 text-center font-mono text-[12px]">
              OPEN ANALYZER →
            </Link>
          </Card>
          <p className="mt-3 font-mono text-[11px] leading-relaxed text-fog">
            .IQ keeps full I+jQ phase — PSK/QAM hold. .wav is BW-limited PCM — FSK previews, QAM collapses. The Compare tab shows the loss in dB.
          </p>
        </aside>
      </div>

      <div className="mt-14">
        <p className="kicker">Pipeline</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PIPELINE.map((s) => (
            <Card key={s.n} className="p-4">
              <p className="font-mono text-[12px] font-bold text-signal">{s.n}</p>
              <p className="mt-1 font-display text-sm font-bold text-paper">{s.t}</p>
              <p className="mt-1 text-[12px] leading-relaxed text-fog">{s.d}</p>
            </Card>
          ))}
        </div>
      </div>

      <div id="download" className="mt-14 scroll-mt-24">
        <p className="kicker">02 // Offline proof</p>
        <div className="mt-4">
          <DownloadExe />
        </div>
      </div>
    </div>
  );
}
