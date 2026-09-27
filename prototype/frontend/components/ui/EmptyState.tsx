export default function EmptyState({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="signit-card flex min-w-0 flex-col items-center p-6 text-center sm:p-8">
      <span
        aria-hidden="true"
        className="flex h-10 w-10 items-center justify-center rounded-md border border-line bg-console"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path
            d="M2 9h2l2-5 3 10 2.5-6.5 1.5 1.5H16"
            stroke="#0E7C6B"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <p className="mt-3 font-display text-base font-bold text-paper">{title}</p>
      <p className="mt-1 max-w-md text-[13px] leading-relaxed text-fog">{body}</p>
    </div>
  );
}
