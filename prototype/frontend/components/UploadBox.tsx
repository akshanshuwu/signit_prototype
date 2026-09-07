"use client";

import { useState } from "react";

const MAX_MB = 15;

export default function UploadBox() {
  const [msg, setMsg] = useState<string | null>(null);

  function checkFile(f: File | undefined) {
    if (!f) return;
    const okExt = /\.(iq|wav|bin)$/i.test(f.name);
    if (!okExt) {
      setMsg(`${f.name} isn't supported — please use .iq, .wav or .bin files.`);
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setMsg(`${f.name} is ${(f.size / 1048576).toFixed(1)} MB — files up to ${MAX_MB} MB are accepted. Try a sample capture below.`);
      return;
    }
    setMsg(`${f.name} passed validation. Prototype demo mode — showing sample result. Full blind decode in production. Open a sample capture below to explore the full analysis.`);
  }

  return (
    <div>
      <label className="block cursor-pointer rounded-xl border border-dashed border-slate-700 bg-slate-900/40 p-8 text-center text-sm text-slate-400 transition hover:border-emerald-600 hover:bg-slate-900/70">
        Drop an .iq, .wav or .bin file here, or click to browse
        <span className="mt-1 block text-xs text-slate-500">Up to {MAX_MB} MB</span>
        <input
          type="file"
          accept=".iq,.wav,.bin"
          className="hidden"
          onChange={(e) => checkFile(e.target.files?.[0])}
        />
      </label>
      {msg && <p className="mt-2 rounded-lg border border-amber-800/60 bg-amber-950/60 p-2.5 text-xs text-amber-200">{msg}</p>}
      <p className="mt-2 text-xs text-slate-500">Sample captures below ship with complete spectrum, modulation and bit-stream analysis.</p>
    </div>
  );
}
