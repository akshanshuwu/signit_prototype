import Link from "next/link";

const SAMPLES = [
  { id: "bpsk", mod: "BPSK", desc: "Binary phase-shift keying · 2k sym/s" },
  { id: "qpsk", mod: "QPSK", desc: "Quadrature PSK · 2k sym/s" },
  { id: "qam16", mod: "16QAM", desc: "16-point QAM · 2k sym/s" },
  { id: "fsk2", mod: "2FSK", desc: "Binary FSK · dev 2 kHz" }
];

const STEPS = [
  { n: "01", t: "Estimate", d: "Sampling rate, bandwidth, carrier offset and SNR from the raw capture." },
  { n: "02", t: "Classify", d: "Modulation type with confidence, backed by spectral and statistical features." },
  { n: "03", t: "Visualize", d: "Spectrum, waterfall, constellation and eye views of the same signal." },
  { n: "04", t: "Decode", d: "Demodulation preview with bit stream, hex view and sync correlation." }
];

export default function LandingPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-14">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">RF signal analysis</p>
      <h1 className="mt-3 max-w-2xl text-4xl font-bold leading-tight text-slate-50 sm:text-5xl">
        Analyze <span className="text-emerald-400">.IQ</span> and <span className="text-emerald-400">.wav</span> captures
      </h1>
      <p className="mt-4 max-w-2xl text-slate-400">
        Drop a recording to estimate its parameters — modulation, sampling rate, symbol rate, SNR —
        then inspect the spectrum, waterfall and constellation and preview the demodulated bit stream.
      </p>
      <div className="mt-7 flex flex-wrap gap-3">
        <Link href="/analyze" className="rounded-lg bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-slate-950 hover:bg-emerald-400">
          Open analyzer
        </Link>
        <Link href="/analyze/qpsk" className="rounded-lg border border-slate-700 px-5 py-2.5 text-sm font-medium text-slate-200 hover:border-slate-500 hover:bg-slate-900">
          View sample analysis
        </Link>
      </div>

      <div className="mt-10 grid grid-cols-3 gap-3 text-center text-sm">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><p className="text-xl font-bold text-slate-50">4</p><p className="text-slate-400">signal types</p></div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><p className="text-xl font-bold text-slate-50">6</p><p className="text-slate-400">analysis views</p></div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><p className="text-xl font-bold text-slate-50">100%</p><p className="text-slate-400">in-browser</p></div>
      </div>

      <div className="mt-10 grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h2 className="font-semibold text-slate-100">.IQ — complex baseband</h2>
          <p className="mt-1 text-sm leading-relaxed text-slate-400">I + jQ samples preserving amplitude and phase. Interpreted with its sampling rate, center frequency and data format. Best for PSK and QAM.</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h2 className="font-semibold text-slate-100">.wav — real audio / IF</h2>
          <p className="mt-1 text-sm leading-relaxed text-slate-400">PCM recording, bandwidth-limited with partial phase information. Good for FSK and FM preview; QAM constellations degrade.</p>
        </div>
      </div>

      <div className="mt-10">
        <p className="text-sm font-semibold text-slate-200">How it works</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <div key={s.n} className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <p className="text-xs font-bold text-emerald-400">{s.n}</p>
              <p className="mt-1 text-sm font-semibold text-slate-100">{s.t}</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-400">{s.d}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-10">
        <div className="flex items-baseline justify-between">
          <p className="text-sm font-semibold text-slate-200">Sample captures</p>
          <Link href="/analyze" className="text-xs font-medium text-emerald-400 hover:text-emerald-300">Open analyzer →</Link>
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          {SAMPLES.map((s) => (
            <Link key={s.id} href={`/analyze/${s.id}`} className="group rounded-xl border border-slate-800 bg-slate-900/50 p-4 hover:border-emerald-600">
              <p className="font-bold text-slate-50">{s.mod}</p>
              <p className="mt-1 text-xs text-slate-400">{s.desc}</p>
              <p className="mt-3 text-xs font-medium text-emerald-400 group-hover:text-emerald-300">Open analysis →</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
