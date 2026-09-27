"use client";

import { useRef, useState } from "react";
import { parseWav, parseRawIQ, parseWavSliced, parseRawIQSliced, type DtypeLabel, type IQData } from "../lib/dsp/parse";
import { analyzeIQ } from "../lib/dsp/toDemo";
import Spinner from "./ui/Spinner";
import type { DemoJson } from "../lib/analysis";

const MAX_MB = 100;
/** Files above this use head-slice reading so RAM stays flat. */
const SLICE_THRESHOLD_BYTES = 15 * 1024 * 1024;

interface Props {
  onResult: (data: DemoJson, ms: number, iq: IQData) => void;
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

  const busy = status === "decoding" || status === "analyzing";

  async function handleFile(f: File | undefined) {
    if (!f || busy) return;
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
        iq.fileSizeBytes = f.size;
        onResult(demo, ms, iq);
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
      iq.fileSizeBytes = f.size;
      onResult(demo, ms, iq);
    } catch (e: any) {
      const m = e?.message ?? "Analysis failed.";
      setMsg(m);
      setStatus("error");
      onError(m);
    }
  }

  return (
    <div className="console-frame min-w-0 p-4">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 font-mono text-[11px] tracking-[0.18em] text-fog">
        <p className="shrink-0">SIGNAL INPUT</p>
        <p className="shrink-0">ACCEPT .iq / .wav / .bin</p>
      </div>
      <div
        role="button"
        tabIndex={busy ? -1 : 0}
        aria-disabled={busy}
        aria-busy={busy}
        onClick={() => { if (!busy) inputRef.current?.click(); }}
        onKeyDown={(e) => { if (e.key === "Enter" && !busy) inputRef.current?.click(); }}
        onDragOver={(e) => { e.preventDefault(); if (!busy) setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files?.[0]); }}
        className={`mt-3 block min-w-0 rounded-md border border-dashed p-4 text-sm break-words transition sm:p-6 ${
          busy ? "cursor-wait opacity-80" : "cursor-pointer"
        } ${
          drag && !busy ? "border-signal bg-signal/10 text-paper" : "border-line bg-console text-paper hover:border-signal"
        }`}
      >
        {busy ? (
          <span className="flex flex-wrap items-center gap-3">
            <span className="font-mono text-[13px] font-bold text-signal">
              {status === "decoding" ? "DECODING…" : "ANALYZING…"}
            </span>
            <Spinner label={status === "decoding" ? "Reading signal…" : "Measuring spectrum…"} />
          </span>
        ) : (
          <span><span className="font-bold">Drop capture file</span> <span className="text-fog">or click to browse — ≤{MAX_MB} MB, on-device</span></span>
        )}
        {(status === "decoding" || status === "analyzing") && (
          <span className="mt-3 block h-1 max-w-md overflow-hidden bg-line">
            <span className="signit-scan block h-full w-1/3 bg-signal" />
          </span>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".iq,.wav,.bin"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
      <div className="mt-3 grid min-w-0 grid-cols-1 gap-px border border-line bg-line font-mono text-[12px] sm:grid-cols-3">
        <label className="bg-panel p-2.5" title="Sampling rate used to interpret raw .iq/.bin. Ignored for .wav (header wins).">
          <span className="block text-fog">FS <span className="text-fog/70">(.iq)</span></span>
          <select disabled={busy} value={fs} onChange={(e) => setFs(Number(e.target.value))} className="mt-1 w-full bg-transparent text-paper disabled:opacity-50">
            {[48000, 96000, 192000, 1000000].map((v) => (
              <option key={v} value={v} className="bg-panel">{v >= 1000000 ? "1M" : `${v / 1000}k`}</option>
            ))}
          </select>
        </label>
        <label className="bg-panel p-2.5" title="Center frequency tag attached to the analysis (does not resample).">
          <span className="block text-fog">FC</span>
          <select disabled={busy} value={fc} onChange={(e) => setFc(Number(e.target.value))} className="mt-1 w-full bg-transparent text-paper disabled:opacity-50">
            {[0, 100000, 1000000].map((v) => (
              <option key={v} value={v} className="bg-panel">{v === 0 ? "0 base" : v >= 1000000 ? "1M" : `${v / 1000}k`}</option>
            ))}
          </select>
        </label>
        <label className="bg-panel p-2.5" title="Binary layout of .iq/.bin: int16 interleaved I/Q (default), float32 I/Q, or uint8 RTL-SDR offset binary.">
          <span className="block text-fog">FORMAT</span>
          <select disabled={busy} value={dtype} onChange={(e) => setDtype(e.target.value as DtypeLabel)} className="mt-1 w-full bg-transparent text-paper disabled:opacity-50">
            <option value="int16" className="bg-panel">int16 IQ</option>
            <option value="float32" className="bg-panel">float32 IQ</option>
            <option value="uint8" className="bg-panel">uint8 RTL</option>
          </select>
        </label>
      </div>
      {msg && (
        <p className={`mt-2 min-w-0 break-words rounded-md border p-2.5 font-mono text-[12px] ${status === "error" ? "border-warn/60 bg-warn/10 text-warn" : "border-line bg-console text-fog"}`}>
          {msg}
        </p>
      )}
    </div>
  );
}
