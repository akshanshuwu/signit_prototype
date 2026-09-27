"use client";

// Modular jsPDF report builder. Each section is a small function so new
// analysis sections can be added later. Only sections with real data are
// included — nothing is invented, nothing is a webpage screenshot.

import type { DemoJson } from "./analysis";
import type { IQData } from "./dsp/parse";
import { spectrumPng, waterfallPng, constellationPng, corrPng, waveformPng } from "./plot-images";

export interface ReportInput {
  demo: DemoJson;
  iq: IQData;
  mono: Float32Array | null;
}

const M = 15; // page margin mm
const PW = 210;
const CW = PW - M * 2; // content width 180mm
const INK: [number, number, number] = [26, 30, 34];
const ACCENT: [number, number, number] = [14, 124, 107];
const MUTED: [number, number, number] = [107, 114, 128];

/** SIGNIT_Report_<original-stem>.pdf with a filesystem-safe stem. */
export function reportFilename(original: string): string {
  const stem = original.replace(/\.[^.]+$/, "") || "capture";
  const safe = stem.replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 60) || "capture";
  return `SIGNIT_Report_${safe}.pdf`;
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}

type Doc = import("jspdf").jsPDF;

function ensureSpace(doc: Doc, y: number, need: number): number {
  if (y + need > 297 - M) {
    doc.addPage();
    return M;
  }
  return y;
}

function h2(doc: Doc, y: number, text: string): number {
  y = ensureSpace(doc, y, 16);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.setTextColor(...ACCENT);
  doc.text(text, M, y);
  return y + 7;
}

function kv(doc: Doc, y: number, k: string, v: string): number {
  y = ensureSpace(doc, y, 7);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10);
  doc.setTextColor(...INK);
  doc.text(`${k}:`, M, y);
  doc.setFont("helvetica", "normal");
  const lines = doc.splitTextToSize(v, CW - 52) as string[];
  doc.text(lines, M + 52, y);
  return y + Math.max(1, lines.length) * 5.2;
}

function para(doc: Doc, y: number, text: string, size = 10): number {
  doc.setFont("helvetica", "normal");
  doc.setFontSize(size);
  doc.setTextColor(...INK);
  const lines = doc.splitTextToSize(text, CW) as string[];
  for (const ln of lines) {
    y = ensureSpace(doc, y, 6);
    doc.text(ln, M, y);
    y += 5.2;
  }
  return y + 2;
}

function monoBlock(doc: Doc, y: number, text: string, maxChars = 1200): number {
  const clipped = text.length > maxChars ? text.slice(0, maxChars) + " …[truncated]" : text;
  doc.setFont("courier", "normal");
  doc.setFontSize(8.5);
  doc.setTextColor(...INK);
  const lines = doc.splitTextToSize(clipped, CW) as string[];
  for (const ln of lines) {
    y = ensureSpace(doc, y, 5);
    doc.text(ln, M, y);
    y += 4.4;
  }
  return y + 2;
}

/** Adds a PNG dataURL fitted to content width; returns new y. Null-safe. */
function figure(doc: Doc, y: number, img: string | null, aspect: number, caption: string): number {
  if (!img) return y;
  const h = CW / aspect;
  y = ensureSpace(doc, y, h + 12);
  doc.addImage(img, "PNG", M, y, CW, h);
  y += h + 2;
  doc.setFont("helvetica", "italic");
  doc.setFontSize(9);
  doc.setTextColor(...MUTED);
  doc.text(caption, M, y);
  return y + 8;
}

export async function buildReportPdf(input: ReportInput): Promise<{ blob: Blob; filename: string }> {
  const { jsPDF } = await import("jspdf");
  const { demo, iq, mono } = input;
  const p = demo.predictions;

  // Render all figures in parallel from the ACTUAL current results.
  const [specImg, fallImg, constImg, corrImg] = await Promise.all([
    spectrumPng(demo),
    waterfallPng(demo),
    constellationPng(demo),
    corrPng(demo),
  ]);
  const waveImg = waveformPng(mono);

  const doc = new jsPDF({ unit: "mm", format: "a4" });
  let y = M;

  // ---- Header ----
  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.setTextColor(...ACCENT);
  doc.text("SIGNIT", M, y);
  y += 8;
  doc.setFontSize(14);
  doc.setTextColor(...INK);
  doc.text("Signal Analysis Report", M, y);
  y += 7;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(...MUTED);
  const dt = new Date().toLocaleString();
  doc.text(`Generated ${dt} · in-browser analysis, no upload`, M, y);
  y += 10;

  // ---- 1. File Information ----
  y = h2(doc, y, "1. File Information");
  const ext = (iq.fileName.match(/\.[^.]+$/)?.[0] ?? "").toLowerCase() || "unknown";
  y = kv(doc, y, "File", iq.fileName);
  y = kv(doc, y, "Type", `${ext} (${iq.kind === "wav" ? "PCM audio" : "complex I/Q"})`);
  if (iq.fileSizeBytes) y = kv(doc, y, "Size", formatBytes(iq.fileSizeBytes));
  y = kv(doc, y, "Samples", iq.i.length.toLocaleString());
  y = kv(doc, y, "Sample rate", `${iq.fs} Hz`);
  y = kv(doc, y, "Duration", `${(iq.i.length / iq.fs).toFixed(2)} s`);
  if (iq.channels) y = kv(doc, y, "Channels", String(iq.channels));
  if (iq.previewNote) y = kv(doc, y, "Preview", iq.previewNote);
  y += 4;

  // ---- 2. Signal Parameters ----
  y = h2(doc, y, "2. Signal Parameters");
  y = kv(doc, y, "Modulation", `${p.modulation} (${Math.round(p.confidence * 100)}% confidence)`);
  y = kv(doc, y, "Symbol rate", `${p.symbol_rate_est} sym/s`);
  y = kv(doc, y, "Bandwidth", `${(p.bw_est / 1000).toFixed(1)} kHz`);
  y = kv(doc, y, "SNR", `${p.snr_est.toFixed(1)} dB`);
  y = kv(doc, y, "Votes", `CNN ${(p.votes.CNN * 100).toFixed(0)}% ${p.modulation} · cumulants ${p.votes.cumulants}`);
  if (demo.meta.center_freq) y = kv(doc, y, "Center freq", `${demo.meta.center_freq} Hz`);
  y += 4;

  // ---- 3. Waveform ----
  if (waveImg) {
    y = h2(doc, y, "3. Waveform Analysis");
    y = figure(doc, y, waveImg, 1000 / 260, "Waveform overview (RMS peaks, full preview).");
    y += 2;
  }

  // ---- 4. Spectrum ----
  y = h2(doc, y, waveImg ? "4. Frequency / Spectrum Analysis" : "3. Frequency / Spectrum Analysis");
  y = figure(doc, y, specImg, 1000 / 520, "FIG.01 — Welch PSD, 512 points.");
  y += 2;

  // ---- 5. Waterfall ----
  const n5 = waveImg ? "5" : "4";
  y = h2(doc, y, `${n5}. Waterfall / Spectrogram`);
  y = figure(doc, y, fallImg, 1000 / 520, "FIG.02 — STFT 128x64, time x frequency.");
  y += 2;

  // ---- 6. Constellation ----
  const n6 = waveImg ? "6" : "5";
  y = h2(doc, y, `${n6}. Constellation Analysis`);
  y = figure(doc, y, constImg, 1000 / 520, `FIG.03 — I/Q scatter (${demo.constellation.i.length} symbols).`);
  y += 2;

  // ---- 7. Demodulation & Decoding ----
  const n7 = waveImg ? "7" : "6";
  y = h2(doc, y, `${n7}. Demodulation & Decoding`);
  y = kv(doc, y, "Sync peak", `lag ${demo.bits_preview.corr_peak.lag} · value ${demo.bits_preview.corr_peak.value.toFixed(2)}`);
  y = figure(doc, y, corrImg, 1000 / 520, "Sync correlation vs lag.");
  y = para(doc, y, "Hex preview (first 32 bytes):");
  y = monoBlock(doc, y, demo.bits_preview.hex);
  y = para(doc, y, "ASCII preview:");
  y = monoBlock(doc, y, demo.bits_preview.ascii, 600);
  y = kv(doc, y, ".IQ SNR", `${demo.comparator.iq_snr.toFixed(1)} dB`);
  y = kv(doc, y, ".WAV SNR", `${demo.comparator.wav_snr.toFixed(1)} dB`);
  y = para(doc, y, demo.comparator.note, 9);
  y += 4;

  // ---- 8. Summary ----
  const n8 = waveImg ? "8" : "7";
  y = h2(doc, y, `${n8}. Analysis Summary`);
  y = para(
    doc,
    y,
    `Capture ${iq.fileName} was classified as ${p.modulation} with ${Math.round(p.confidence * 100)}% confidence ` +
      `(symbol rate ${p.symbol_rate_est} sym/s, bandwidth ${(p.bw_est / 1000).toFixed(1)} kHz, SNR ${p.snr_est.toFixed(1)} dB).`
  );
  if (demo.log.length > 0) {
    y = para(doc, y, "Processing log:");
    doc.setFont("courier", "normal");
    doc.setFontSize(8.5);
    doc.setTextColor(...INK);
    for (const ln of demo.log.slice(-12)) {
      const lines = doc.splitTextToSize(`$ ${ln}`, CW) as string[];
      for (const l of lines) {
        y = ensureSpace(doc, y, 5);
        doc.text(l, M, y);
        y += 4.4;
      }
    }
    y += 2;
  }

  const blob = doc.output("blob") as Blob;
  return { blob, filename: reportFilename(iq.fileName) };
}
