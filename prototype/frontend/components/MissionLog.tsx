export default function MissionLog({ lines }: { lines: string[] }) {
  return (
    <div className="rounded bg-black/40 p-3 font-mono text-xs text-green-300">
      {lines.length === 0 && <p className="text-slate-500">$ no logs</p>}
      {lines.map((l, idx) => (
        <p key={idx}>$ {l}</p>
      ))}
    </div>
  );
}
