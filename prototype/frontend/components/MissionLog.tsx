export default function MissionLog({ lines }: { lines: string[] }) {
  return (
    <div className="max-h-64 overflow-auto border border-line bg-console p-3 font-mono text-[12px] leading-relaxed text-paper">
      <p className="mb-1 text-[10px] tracking-[0.2em] text-fog">ROOT@SIGNIT:~</p>
      {lines.length === 0 && <p className="text-fog">$ no logs</p>}
      {lines.map((l, idx) => (
        <p key={idx} className="whitespace-pre-wrap"><span className="text-signal">$</span> {l}</p>
      ))}
    </div>
  );
}
