interface Props {
  iqSnr: number;
  wavSnr: number;
  note: string;
}

export default function Comparator({ iqSnr, wavSnr, note }: Props) {
  const loss = iqSnr - wavSnr;
  const max = Math.max(iqSnr, wavSnr, 1);
  return (
    <div className="font-mono text-[12px]">
      <div className="grid gap-px border border-line bg-line md:grid-cols-2">
        <div className="bg-panel p-3">
          <p className="text-fog">.IQ · COMPLEX</p>
          <p className="mt-1 font-display text-xl font-bold text-signal">{iqSnr.toFixed(1)} dB</p>
          <div className="mt-2 h-1.5 bg-line">
            <div className="h-full bg-signal" style={{ width: `${(iqSnr / max) * 100}%` }} />
          </div>
        </div>
        <div className="bg-panel p-3">
          <p className="text-fog">.WAV · BW-LIMITED</p>
          <p className="mt-1 font-display text-xl font-bold">{wavSnr.toFixed(1)} dB</p>
          <div className="mt-2 h-1.5 bg-line">
            <div className="h-full bg-fog" style={{ width: `${(wavSnr / max) * 100}%` }} />
          </div>
        </div>
      </div>
      <p className="mt-3 text-fog">
        LOSS <span className="font-bold text-warn">{loss.toFixed(1)} dB</span> — {note}
      </p>
    </div>
  );
}
