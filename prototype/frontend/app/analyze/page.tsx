import Link from "next/link";
import UploadBox from "../../components/UploadBox";
import { DEMO_IDS } from "../../lib/demo";

const META: Record<string, { mod: string; desc: string }> = {
  bpsk: { mod: "BPSK", desc: "Binary PSK · 2k sym/s · fs 48k" },
  qpsk: { mod: "QPSK", desc: "Quadrature PSK · 2k sym/s · fs 48k" },
  qam16: { mod: "16QAM", desc: "16-point QAM · 2k sym/s · fs 48k" },
  fsk2: { mod: "2FSK", desc: "Binary FSK · dev 2 kHz · fs 48k" }
};

export default function AnalyzePage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Link href="/" className="text-xs font-medium text-slate-500 hover:text-slate-300">← Home</Link>
      <h1 className="mt-2 text-2xl font-bold text-slate-50">Analyze a capture</h1>
      <p className="mt-1 text-sm text-slate-400">Drop an .iq, .wav or .bin recording — or open a sample capture with full analysis.</p>
      <div className="mt-6">
        <UploadBox />
      </div>
      <h2 className="mt-10 text-sm font-semibold text-slate-200">Sample captures</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-4">
        {DEMO_IDS.map((id) => (
          <Link key={id} href={`/analyze/${id}`} className="group rounded-xl border border-slate-800 bg-slate-900/50 p-4 hover:border-emerald-600">
            <p className="font-bold text-slate-50">{META[id].mod}</p>
            <p className="mt-1 text-xs text-slate-400">{META[id].desc}</p>
            <p className="mt-3 text-xs font-medium text-emerald-400 group-hover:text-emerald-300">Open analysis →</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
