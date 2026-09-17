// Assemble real-file analysis into frozen DemoJson contract.
import type { DemoJson } from "../analysis";
import type { IQData } from "./parse";
import { computePSD, computeSpectrogram, constellationDecimate } from "./spectrum";
import { estimateSnrBw, estimateSymbolRate, classify } from "./estimate";
import { bitsPreview } from "./bits";

export function analyzeIQ(data: IQData, centerFreq = 0): DemoJson {
  const t0 = performance.now();
  const { i, q, fs, fileName, kind } = data;

  const psd = computePSD(i, q, fs);
  const spec = computeSpectrogram(i, q, fs);
  const cons = constellationDecimate(i, q, 2000);
  const { snr, bw } = estimateSnrBw(psd.freqs, psd.mags_db);
  const symbol = estimateSymbolRate(i, q, fs);
  const cls = classify(i, q);
  const bits = bitsPreview(i, q, cls.mod);

  const wavSnr = kind === "wav" ? snr : Math.max(0, snr - 3.0);
  const note =
    kind === "wav"
      ? "Real PCM path: BW-limited, partial phase — FSK/FM reliable, QAM degraded."
      : ".wav equivalent estimated 3 dB lower: real-only path loses phase BW.";

  const ms = Math.round(performance.now() - t0);
  const ingestLine = data.previewNote
    ? `ingest ok: ${i.length} samples (${data.previewNote}) · fs ${fs} Hz · ${kind}`
    : `ingest ok: ${i.length} samples · fs ${fs} Hz · ${kind}`;
  const log = [
    ingestLine,
    `psd ok: 512 pts · spectrogram ${spec.freqs.length}x${spec.times.length}`,
    `est: symbol ${symbol} sym/s · bw ${Math.round(bw)} Hz · snr ${snr.toFixed(1)} dB`,
    `classify=${cls.mod} conf ${(cls.conf * 100).toFixed(0)}% · cumulants=${cls.cumulants}`,
    `bits: 32B preview · corr lag ${bits.corr_peak.lag} val ${bits.corr_peak.value.toFixed(2)} · ${ms}ms in-browser`,
  ];

  return {
    meta: { modulation: cls.mod, fs, symbol_rate: symbol, snr_db: Math.round(snr * 10) / 10, center_freq: centerFreq, file: fileName },
    predictions: {
      modulation: cls.mod,
      confidence: Math.round(cls.conf * 100) / 100,
      votes: { CNN: Math.round(cls.conf * 100) / 100, cumulants: cls.cumulants },
      fs_est: fs,
      symbol_rate_est: symbol,
      bw_est: Math.round(bw),
      snr_est: Math.round(snr * 10) / 10,
    },
    psd: { freqs: psd.freqs, mags_db: psd.mags_db },
    spectrogram: { times: spec.times, freqs: spec.freqs, z_db: spec.z_db },
    constellation: cons,
    bits_preview: bits,
    comparator: { iq_snr: Math.round(snr * 10) / 10, wav_snr: Math.round(wavSnr * 10) / 10, note },
    log,
  };
}
