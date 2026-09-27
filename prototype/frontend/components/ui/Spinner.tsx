export default function Spinner({ label = "Processing…" }: { label?: string }) {
  return (
    <span
      role="status"
      aria-live="polite"
      className="inline-flex items-center gap-2 font-mono text-[12px] text-fog"
    >
      <svg
        className="signit-spinner h-4 w-4"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <circle cx="8" cy="8" r="6.5" stroke="#E7E0D3" strokeWidth="2" />
        <path
          d="M14.5 8a6.5 6.5 0 0 0-6.5-6.5"
          stroke="#0E7C6B"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
      {label}
    </span>
  );
}
