import type { Metadata } from "next";
import Card from "../../components/ui/Card";
import {
  DOWNLOAD_URL,
  EXE_VERSION,
  EXE_SIZE,
  EXE_SHA256,
  HAS_DIRECT_DOWNLOAD,
} from "../../lib/download";

export const metadata: Metadata = {
  title: "SIGNIT for Windows — Download",
  description:
    "Download SIGNIT for Windows: a standalone desktop application for analyzing .wav and .iq signal files.",
};

/** Subtle SIGNIT desktop-app representation — inline SVG, brand palette. */
function AppVisual() {
  return (
    <svg
      viewBox="0 0 320 190"
      className="h-auto w-full"
      role="img"
      aria-label="SIGNIT desktop application preview"
    >
      <rect x="8" y="8" width="304" height="174" rx="10" fill="#FFFFFF" stroke="#E7E0D3" />
      <rect x="8" y="8" width="304" height="30" rx="10" fill="#F4EFE6" />
      <rect x="8" y="28" width="304" height="10" fill="#F4EFE6" />
      <circle cx="26" cy="23" r="4" fill="#E7E0D3" />
      <circle cx="40" cy="23" r="4" fill="#E7E0D3" />
      <circle cx="54" cy="23" r="4" fill="#E7E0D3" />
      <rect x="70" y="19" width="90" height="8" rx="4" fill="#E7E0D3" />
      {/* spectrum trace */}
      <path
        d="M24 110 L52 110 L66 84 L80 96 L96 66 L112 78 L128 58 L144 72 L160 64 L176 88 L192 74 L208 92 L224 70 L240 82 L256 68 L272 86 L296 80"
        fill="none"
        stroke="#0E7C6B"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <line x1="24" y1="122" x2="296" y2="122" stroke="#E7E0D3" />
      {/* frequency bars */}
      {Array.from({ length: 24 }, (_, b) => {
        const hgt = 8 + ((b * 37) % 26);
        return (
          <rect
            key={b}
            x={24 + b * 11.5}
            y={168 - hgt}
            width="7"
            height={hgt}
            rx="2"
            fill={b % 4 === 0 ? "#0E7C6B" : "#16A34A"}
            opacity="0.85"
          />
        );
      })}
    </svg>
  );
}

export default function DownloadPage() {
  return (
    <div className="mx-auto w-full min-w-0 max-w-xl px-4 py-10 text-center sm:px-6 sm:py-14">
      <p className="kicker mx-auto inline-block">Windows build</p>
      <h1 className="mt-4 font-display text-3xl font-bold tracking-tight text-paper sm:text-4xl">
        SIGNIT for Windows
      </h1>
      <p className="mx-auto mt-3 max-w-md text-[14px] leading-relaxed text-fog">
        A standalone Windows application for analyzing{" "}
        <span className="font-mono">.wav</span> and <span className="font-mono">.iq</span>{" "}
        signal files with SIGNIT.
      </p>

      <div className="signit-enter mx-auto mt-8 w-full max-w-md overflow-hidden rounded-md border border-line bg-white p-3 shadow-subtle">
        <AppVisual />
      </div>

      <Card className="mx-auto mt-6 w-full max-w-md p-6 text-center">
        <p className="font-mono text-[11px] tracking-[0.2em] text-fog">
          LATEST WINDOWS BUILD
          {EXE_VERSION && <> · {EXE_VERSION}</>}
        </p>
        <p className="mt-2 font-display text-xl font-bold text-paper">SIGNIT Windows Build</p>
        <ul className="mt-3 space-y-1 font-mono text-[12px] text-fog">
          <li>Windows desktop application</li>
          <li>Latest build{EXE_SIZE && <> · {EXE_SIZE}</>}</li>
          <li>.exe installer</li>
        </ul>
        <a
          href={DOWNLOAD_URL}
          {...(HAS_DIRECT_DOWNLOAD
            ? { download: true }
            : { target: "_blank", rel: "noreferrer" })}
          className="btn-primary mt-5 block px-5 py-3 font-mono text-[13px]"
        >
          DOWNLOAD FOR WINDOWS
        </a>
        {!HAS_DIRECT_DOWNLOAD && (
          <p className="mt-3 text-[12px] leading-relaxed text-fog">
            The packaged .exe is in final assembly — this opens GitHub Releases,
            where the installer will appear.
          </p>
        )}
        {EXE_SHA256 && (
          <p className="mt-3 break-all font-mono text-[11px] text-fog">SHA256 {EXE_SHA256}</p>
        )}
      </Card>

      <p className="mt-6 font-mono text-[11px] text-fog">Windows 10/11 recommended.</p>
    </div>
  );
}
