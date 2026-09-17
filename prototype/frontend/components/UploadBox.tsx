"use client";

import { useRef, useState } from "react";
import { parseWav, parseRawIQ, parseWavSliced, parseRawIQSliced, type DtypeLabel } from "../lib/dsp/parse";
import { analyzeIQ } from "../lib/dsp/toDemo";
import type { DemoJson } from "../lib/analysis";

const MAX_MB = 100;
/** Files above this use head-slice reading so RAM stays flat. */
const SLICE_THRESHOLD_BYTES = 15 * 1024 * 1024;

interface Props {
  onResult: (data: DemoJson, ms: number) => void;
  onError: (msg: string) => void;
}

type Status = "idle" | "decoding" | "analyzing" | "done" | "error";

export default function UploadBox({ onResult, onError }: Props) {
  const [msg, setMsg] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [drag, setDrag] = useState(false);
  const [fs, setFs] = useState(48000);
  const [fc, setFc] = useState(0);
  const [dtype, setDtype] = useState<DtypeLabel>("int16");
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(f: File | undefined) {
    if (!f) return;
    const okExt = /\.(iq|wav|bin)$/i.test(f.name);
    if (!okExt) {
      const m = `${f.name} isn't supported — please use .iq, .wav or .bin files.`;
      setMsg(m);
      setStatus("error");
      onError(m);
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      const m = `${f.name} is ${(f.size / 1048576).toFixed(1)} MB — files up to ${MAX_MB} MB are accepted.`;
      setMsg(m);
      setStatus("error");
      onError(m);
      return;
    }
    try {
      const isWav = /\.wav$/i.test(f.name);
      const useSlice = f.size > SLICE_THRESHOLD_BYTES;
      const t0 = performance.now();
      if (useSlice) {
        setStatus("decoding");
        setMsg(`Decoding head preview (${(f.size / 1048576).toFixed(1)} MB file)…`);
        const iq = isWav ? await parseWavSliced(f, f.name) : await parseRawIQSliced(f, f.name, fs, dtype);
        setStatus("analyzing");
        setMsg(`Analyzing ${iq.i.length} samples…`);
        await new Promise((r) => setTimeout(r, 30));
        const demo = analyzeIQ(iq, fc);
        const ms = Math.round(performance.now() - t0);
        setStatus("done");
        setMsg(`${f.name} → ${demo.predictions.modulation} ${(demo.predictions.confidence * 100).toFixed(0)}% confidence in ${ms} ms. Full analysis below.`);
        onResult(demo, ms);
        return;
      }
      setStatus("decoding");
      setMsg(`Decoding ${f.name}…`);
      const buf = await f.arrayBuffer();
      const iq = isWav ? await parseWav(buf, f.name) : parseRawIQ(buf, f.name, fs, dtype);
      setStatus("analyzing");
      setMsg(`Analyzing ${iq.i.length} samples…`);
      await new Promise((r) => setTimeout(r, 30));
      const demo = analyzeIQ(iq, fc);
      const ms = Math.round(performance.now() - t0);
      setStatus("done");
      setMsg(`${f.name} → ${demo.predictions.modulation} ${(demo.predictions.confidence * 100).toFixed(0)}% confidence in ${ms} ms. Full analysis below.`);
      onResult(demo, ms);
    } catch (e: any) {
      const m = e?.message ?? "Analysis failed.";
      setMsg(m);
      setStatus("error");
      onError(m);
    }
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => { if (e.key === "Enter") inputRef.current?.click(); }}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files?.[0]); }}
        className={`block cursor-pointer rounded-xl border border-dashed p-8 text-center text-sm transition ${
          drag ? "border-emerald-500 bg-slate-900/70 text-slate-200" : "border-slate-700 bg-slate-900/40 text-slate-400 hover:border-emerald-600 hover:bg-slate-900/70"
        }`}
      >
        {status === "decoding" || status === "analyzing" ? (
          <span>Processing…</span>
        ) : (
          <>Drop an .iq, .wav or .bin file here, or click to browse</>
        )}
        <span className="mt-1 block text-xs text-slate-500">Up to {MAX_MB} MB · analyzed in your browser</span>
        <input
          ref={inputRef}
          type="file"
          accept=".iq,.wav,.bin"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
      <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
        <label className="rounded-lg border border-slate-800 bg-slate-900/40 p-2">
          <span className="block text-slate-500">Sampling rate (for .iq)</span>
          <select value={fs} onChange={(e) => setFs(Number(e.target.value))} className="mt-1 w-full bg-transparent text-slate-200">
            {[48000, 96000, 192000, 1000000].map((v) => (
              <option key={v} value={v} className="bg-slate-900">{v >= 1000000 ? "1M" : `${v / 1000}k`}</option>
            ))}
          </select>
        </label>
        <label className="rounded-lg border border-slate-800 bg-slate-900/40 p-2">
          <span className="block text-slate-500">Center freq</span>
          <select value={fc} onChange={(e) => setFc(Number(e.target.value))} className="mt-1 w-full bg-transparent text-slate-200">
            {[0, 100000, 1000000].map((v) => (
              <option key={v} value={v} className="bg-slate-900">{v === 0 ? "0 (baseband)" : v >= 1000000 ? "1M" : `${v / 1000}k`}</option>
            ))}
          </select>
        </label>
        <label className="rounded-lg border border-slate-800 bg-slate-900/40 p-2">
          <span className="block text-slate-500">Data format</span>
          <select value={dtype} onChange={(e) => setDtype(e.target.value as DtypeLabel)} className="mt-1 w-full bg-transparent text-slate-200">
            <option value="int16" className="bg-slate-900">int16 IQ</option>
            <option value="float32" className="bg-slate-900">float32 IQ</option>
            <option value="uint8" className="bg-slate-900">uint8 RTL</option>
          </select>
        </label>
      </div>
      {msg && (
        <p className={`mt-2 rounded-lg border p-2.5 text-xs ${status === "error" ? "border-red-800/60 bg-red-950/60 text-red-200" : "border-slate-700 bg-slate-900/60 text-slate-300"}`}>
          {msg}
        </p>
      )}
    </div>
  );
}
