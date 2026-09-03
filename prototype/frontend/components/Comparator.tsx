interface Props {
  iqSnr: number;
  wavSnr: number;
  note: string;
}

export default function Comparator({ iqSnr, wavSnr, note }: Props) {
  const loss = iqSnr - wavSnr;
  const max = Math.max(iqSnr, wavSnr, 1);
  return (
    <div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border border-emerald-800/60 bg-emerald-950/30 p-3">
          <p className="text-xs text-slate-400">.IQ (complex, full phase)</p>
          <p className="text-xl font-bold text-emerald-300">{iqSnr.toFixed(1)} dB</p>
          <div className="mt-2 h-2 rounded bg-slate-800">
            <div className="h-2 rounded bg-emerald-500" style={{ width: `${(iqSnr / max) * 100}%` }} />
          </div>
        </div>
        <div className="rounded border border-slate-700 p-3">
          <p className="text-xs text-slate-400">.wav (real, BW-limited)</p>
          <p className="text-xl font-bold text-slate-200">{wavSnr.toFixed(1)} dB</p>
          <div className="mt-2 h-2 rounded bg-slate-800">
            <div className="h-2 rounded bg-slate-400" style={{ width: `${(wavSnr / max) * 100}%` }} />
          </div>
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        Degradation: <span className="font-semibold text-amber-300">{loss.toFixed(1)} dB</span> — {note}
      </p>
    </div>
  );
}
