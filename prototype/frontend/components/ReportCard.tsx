import type { DemoJson } from "../lib/analysis";
import { formatKhz } from "../lib/analysis";

export default function ReportCard({ data }: { data: DemoJson }) {
  const p = data.predictions;
  const pct = Math.round(p.confidence * 100);
  const rows: Array<[string, string]> = [
    ["FS_EST", `${p.fs_est} Hz`],
    ["RS_EST", `${p.symbol_rate_est} sym/s`],
    ["BW_EST", formatKhz(p.bw_est)],
    ["SNR_EST", `${p.snr_est.toFixed(1)} dB`],
    ["VOTE_CNN", `${(p.votes.CNN * 100).toFixed(0)}% ${p.modulation}`],
    ["VOTE_CUM", p.votes.cumulants]
  ];
  return (
    <div>
      <p className="font-mono text-[11px] tracking-[0.2em] text-fog">VERDICT</p>
      <div className="mt-1 flex items-baseline gap-3">
        <p className="font-display text-3xl font-bold tracking-tight">{p.modulation}</p>
        <p className="font-mono text-[13px] font-bold text-signal">{pct}% CONF</p>
      </div>
      <div className="mt-2 h-1.5 bg-line" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} title={`${pct}% confidence`}>
        <div className="h-full bg-signal" style={{ width: `${pct}%` }} />
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-px border border-line bg-line font-mono text-[12px] md:grid-cols-3">
        {rows.map(([k, v]) => (
          <div key={k} className="bg-panel p-2.5">
            <dt className="text-fog">{k}</dt>
            <dd className="mt-0.5 font-bold text-paper">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-2 font-mono text-[11px] text-fog">SRC {data.meta.file} · FS {data.meta.fs} · RS {data.meta.symbol_rate} · SNR {data.meta.snr_db}dB</p>
    </div>
  );
}
