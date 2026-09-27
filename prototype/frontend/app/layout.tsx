import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "SIGNIT — RF Signal Analyzer",
  description: "Upload .IQ or .wav captures for automatic signal parameter estimation, modulation analysis and demodulation preview."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-ink font-sans text-paper antialiased">
        <header className="sticky top-0 z-40 border-b border-line bg-ink/90 backdrop-blur">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3 sm:px-6">
            <Link href="/" className="flex min-w-0 items-center gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-line bg-panel shadow-subtle" aria-hidden="true">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <rect x="1.5" y="6" width="2" height="6" fill="#16A34A" />
                  <rect x="6" y="2.5" width="2" height="9.5" fill="#0E7C6B" />
                  <rect x="10.5" y="8" width="2" height="4" fill="#6B7280" />
                </svg>
              </span>
              <span className="font-display text-sm font-bold tracking-wide">SIGNIT</span>
              <span className="hidden font-mono text-[11px] text-fog md:inline">RF CAPTURE ANALYZER</span>
            </Link>
            <nav className="flex shrink-0 items-center gap-3 font-mono text-[11px] text-fog sm:gap-5 sm:text-[12px]">
              <Link href="/analyze" className="whitespace-nowrap hover:text-paper"><span className="mr-1 text-signal">01</span>ANALYZER</Link>
              <Link href="/#download" className="whitespace-nowrap rounded-md border border-line bg-panel px-2.5 py-1.5 text-paper shadow-subtle hover:border-signal">
                <span className="mr-1 text-signal">02</span>WINDOWS BUILD
              </Link>
            </nav>
          </div>
        </header>
        <main className="min-w-0">{children}</main>
        <footer className="border-t border-line bg-panel/60">
          <div className="mx-auto grid max-w-6xl gap-3 px-4 py-8 font-mono text-[11px] leading-relaxed text-fog sm:px-6 md:grid-cols-3">
            <p>SIGNIT · spectrum / modulation / bit-stream analysis for .IQ + .wav captures. 100% in-browser.</p>
            <p>RESULT CONTRACT v1 · PSD 512pt · STFT 128×64 · SYMBOLS ≤2000 · HEAD PREVIEW 262144</p>
            <p className="md:text-right">
              <Link href="/analyze" className="hover:text-paper">ANALYZER</Link>
              {" — "}
              <Link href="/#download" className="text-signal">WINDOWS BUILD</Link>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
