import Link from "next/link";
import DownloadExe from "../components/DownloadExe";

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
    <div className="mx-auto max-w-6xl px-6 pb-16">
      <div className="grid gap-8 pt-12 lg:grid-cols-12">
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
            <Link href="/analyze" className="bg-signal px-5 py-2.5 font-mono text-[13px] font-bold text-ink hover:brightness-110">
              OPEN ANALYZER
            </Link>
            <Link href="#download" className="border border-line bg-panel px-5 py-2.5 font-mono text-[13px] text-paper hover:border-signal">
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
        <aside className="lg:col-span-4">
          <div className="console-frame p-4">
            <p className="font-mono text-[11px] tracking-[0.2em] text-fog">FIELD RECORD · EXAMPLE</p>
            <div className="mt-3 space-y-2 font-mono text-[12px]">
              <div className="flex justify-between border-b border-line pb-2"><span className="text-fog">FILE</span><span>qpsk_48k.iq</span></div>
              <div className="flex justify-between border-b border-line pb-2"><span className="text-fog">FS</span><span>48000 Hz</span></div>
              <div className="flex justify-between border-b border-line pb-2"><span className="text-fog">VERDICT</span><span className="text-signal">QPSK · 94%</span></div>
              <div className="flex justify-between border-b border-line pb-2"><span className="text-fog">SNR</span><span>14.8 dB</span></div>
              <div className="flex justify-between"><span className="text-fog">BW</span><span>4.0 kHz</span></div>
            </div>
            <Link href="/analyze" className="mt-4 block border border-line bg-console px-3 py-2 text-center font-mono text-[12px] text-paper hover:border-signal">
              RUN THIS CAPTURE →
            </Link>
          </div>
          <p className="mt-3 font-mono text-[11px] leading-relaxed text-fog">
            .IQ keeps full I+jQ phase — PSK/QAM hold. .wav is BW-limited PCM — FSK previews, QAM collapses. The Compare tab shows the loss in dB.
          </p>
        </aside>
      </div>

      <div className="mt-14">
        <p className="kicker">Pipeline</p>
        <div className="mt-4 grid gap-px border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          {PIPELINE.map((s) => (
            <div key={s.n} className="bg-panel p-4">
              <p className="font-mono text-[12px] font-bold text-signal">{s.n}</p>
              <p className="mt-1 font-display text-sm font-bold">{s.t}</p>
              <p className="mt-1 text-[12px] leading-relaxed text-fog">{s.d}</p>
            </div>
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
