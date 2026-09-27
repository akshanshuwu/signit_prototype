export default function SectionTitle({
  kicker,
  title,
  hint,
}: {
  kicker?: string;
  title: string;
  hint?: string;
}) {
  return (
    <div className="min-w-0">
      {kicker && <p className="kicker">{kicker}</p>}
      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-lg font-bold tracking-tight text-paper">
          {title}
        </h2>
        {hint && (
          <p className="font-mono text-[11px] text-fog">{hint}</p>
        )}
      </div>
    </div>
  );
}
