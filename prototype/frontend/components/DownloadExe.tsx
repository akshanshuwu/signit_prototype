"use client";

const EXE_URL = process.env.NEXT_PUBLIC_EXE_URL ?? "";
const EXE_VERSION = process.env.NEXT_PUBLIC_EXE_VERSION ?? "";
const EXE_SIZE = process.env.NEXT_PUBLIC_EXE_SIZE ?? "";
const EXE_SHA256 = process.env.NEXT_PUBLIC_EXE_SHA256 ?? "";
const RELEASE_URL = process.env.NEXT_PUBLIC_RELEASE_URL ?? "";

export default function DownloadExe({ compact = false }: { compact?: boolean }) {
  if (!EXE_URL) {
    return (
      <div className="border border-line bg-panel p-4">
        <p className="font-mono text-[11px] tracking-[0.2em] text-fog">02 // WINDOWS BUILD</p>
        <p className="mt-1 font-display text-base font-bold">Offline .exe — in final assembly</p>
        <p className="mt-1 text-[12px] leading-relaxed text-fog">
          Full any-file proof runs on Windows (PySide6 · offline · single file). This panel becomes the
          direct download once the Release is published. Web triage above is fully usable now.
        </p>
        {RELEASE_URL && (
          <a href={RELEASE_URL} target="_blank" rel="noreferrer" className="mt-2 inline-block font-mono text-[12px] font-bold text-signal">
            OPEN RELEASES →
          </a>
        )}
      </div>
    );
  }

  return (
    <div className={`console-frame ${compact ? "p-4" : "p-5"}`}>
      <p className="font-mono text-[11px] tracking-[0.2em] text-fog">02 // WINDOWS BUILD {EXE_VERSION && <>· {EXE_VERSION}</>}</p>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
        <p className="font-display text-lg font-bold">SIGNIT for Windows{EXE_SIZE && <span className="ml-2 font-mono text-[12px] font-normal text-fog">{EXE_SIZE}</span>}</p>
        <a href={EXE_URL} download className="bg-signal px-5 py-2.5 font-mono text-[13px] font-bold text-ink hover:brightness-110">
          DOWNLOAD SIGNIT.EXE
        </a>
      </div>
      {EXE_SHA256 && <p className="mt-3 break-all font-mono text-[11px] text-fog">SHA256 {EXE_SHA256}</p>}
      <p className="mt-2 font-mono text-[11px] leading-relaxed text-fog">
        UNSIGNED BUILD: SmartScreen → “More info → Run anyway”. DB: %APPDATA%/SIGNIT/history.db
      </p>
    </div>
  );
}
