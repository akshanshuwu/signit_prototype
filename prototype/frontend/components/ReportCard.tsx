import type { DemoJson } from "../lib/demo";
import { formatKhz } from "../lib/demo";

export default function ReportCard({ data }: { data: DemoJson }) {
  const p = data.predictions;
  const pct = Math.round(p.confidence * 100);
  const rows: Array<[string, string]> = [
    ["Sampling freq (est)", `${p.fs_est} Hz`],
    ["Symbol rate (est)", `${p.symbol_rate_est} sym/s`],
    ["Bandwidth (est)", formatKhz(p.bw_est)],
    ["SNR (est)", `${p.snr_est.toFixed(1)} dB`],
    ["CNN vote", `${(p.votes.CNN * 100).toFixed(0)}% ${p.modulation}`],
    ["Cumulants vote", p.votes.cumulants]
  ];
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className="text-lg font-bold">{p.modulation}</p>
        <p className="text-sm text-cyan-300">{pct}% confidence</p>
      </div>
        <div className="h-2 rounded bg-slate-800" style={{ width: "100%" }}>
          <div className="h-2 rounded bg-emerald-500" style={{ width: `${pct}%` }} />
        </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
        {rows.map(([k, v]) => (
          <div key={k} className="rounded border border-slate-800 p-2">
            <dt className="text-slate-500">{k}</dt>
            <dd className="mt-0.5 font-semibold text-slate-200">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-2 text-xs text-slate-500">File: {data.meta.file} · fs {data.meta.fs} Hz · {data.meta.symbol_rate} sym/s · SNR {data.meta.snr_db} dB</p>
    </div>
  );
}
