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
      <body className="min-h-screen bg-slate-950 text-slate-200 antialiased">
        <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-500 text-sm font-black text-slate-950">S</span>
              <span className="text-sm font-bold tracking-wide text-slate-100">SIGNIT</span>
              <span className="hidden text-xs text-slate-500 sm:inline">RF Signal Analyzer</span>
            </Link>
            <nav className="flex items-center gap-4 text-xs font-medium text-slate-400">
              <Link href="/analyze" className="hover:text-slate-100">Analyzer</Link>
              <Link href="/analyze/qpsk" className="hover:text-slate-100">Sample analysis</Link>
            </nav>
          </div>
        </header>
        <main>{children}</main>
        <footer className="mx-auto max-w-5xl px-6 py-8 text-xs text-slate-600">
          SIGNIT · spectrum, modulation and bit-stream analysis for .IQ and .wav captures
        </footer>
      </body>
    </html>
  );
}
