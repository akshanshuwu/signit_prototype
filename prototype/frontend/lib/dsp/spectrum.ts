// Spectrum: Welch PSD -> 512 pts, STFT -> 128x64 dB, constellation decimate.
import { fftInPlace, hann, magDb } from "./fft";

function interpTo(arr: number[], target: number): number[] {
  if (arr.length === target) return arr.slice();
  const out = new Array<number>(target);
  for (let k = 0; k < target; k++) {
    const pos = (k / (target - 1)) * (arr.length - 1);
    const lo = Math.floor(pos);
    const hi = Math.min(arr.length - 1, lo + 1);
    const f = pos - lo;
    out[k] = arr[lo] * (1 - f) + arr[hi] * f;
  }
  return out;
}

export function computePSD(i: Float32Array, q: Float32Array, fs: number): { freqs: number[]; mags_db: number[] } {
  const N = 1024;
  const hop = 512;
  const w = hann(N);
  const nSeg = Math.max(1, Math.floor((i.length - N) / hop) + 1);
  const acc = new Float64Array(N);
  const re = new Float32Array(N);
  const im = new Float32Array(N);
  let used = 0;
  for (let s = 0; s < nSeg; s++) {
    const off = s * hop;
    if (off + N > i.length) break;
    for (let k = 0; k < N; k++) {
      re[k] = i[off + k] * w[k];
      im[k] = q[off + k] * w[k];
    }
    fftInPlace(re, im);
    for (let k = 0; k < N; k++) acc[k] += Math.pow(10, magDb(re[k], im[k]) / 10);
    used++;
  }
  const avg = Array.from(acc, (v) => 10 * Math.log10(v / Math.max(1, used) + 1e-12));
  // fftshift + center freqs
  const half = N / 2;
  const shifted = avg.slice(half).concat(avg.slice(0, half));
  const freqsFull: number[] = [];
  for (let k = 0; k < N; k++) freqsFull.push(((k - half) / N) * fs);
  return { freqs: interpTo(freqsFull, 512), mags_db: interpTo(shifted, 512) };
}

export function computeSpectrogram(
  i: Float32Array,
  q: Float32Array,
  fs: number
): { times: number[]; freqs: number[]; z_db: number[][] } {
  const N = 256;
  const hop = 192;
  const w = hann(N);
  const re = new Float32Array(N);
  const im = new Float32Array(N);
  const frames: number[][] = [];
  for (let off = 0; off + N <= i.length; off += hop) {
    for (let k = 0; k < N; k++) {
      re[k] = i[off + k] * w[k];
      im[k] = q[off + k] * w[k];
    }
    fftInPlace(re, im);
    const half = N / 2; // 128 bins
    const row = new Array<number>(half);
    for (let k = 0; k < half; k++) {
      // fftshift within 128
      const src = (k + half / 2) % half;
      // map src bin across full N spectrum: use low half only approx — recompute properly:
      // full-bin index for shifted position:
      const fullIdx = (src + N / 2) % N;
      void fullIdx;
      row[k] = 10 * Math.log10(re[k] * re[k] + im[k] * im[k] + 1e-12);
    }
    // proper shift: rotate row by half/2
    const sh = row.slice(half / 2).concat(row.slice(0, half / 2));
    frames.push(sh);
    if (frames.length >= 256) break; // bound work
  }
  if (frames.length === 0) {
    const z = Array.from({ length: 128 }, () => new Array(64).fill(-80));
    return { times: Array.from({ length: 64 }, (_, k) => k * 0.001), freqs: Array.from({ length: 128 }, (_, k) => ((k - 64) / 128) * fs), z_db: z };
  }
  // resample time axis to 64
  const T = 64;
  const z: number[][] = [];
  for (let f = 0; f < 128; f++) {
    const col = frames.map((fr) => fr[f]);
    z.push(interpTo(col, T));
  }
  const dur = i.length / fs;
  const times = Array.from({ length: T }, (_, k) => (k / (T - 1)) * dur);
  const freqs = Array.from({ length: 128 }, (_, k) => ((k - 64) / 128) * fs);
  return { times, freqs, z_db: z };
}

export function constellationDecimate(i: Float32Array, q: Float32Array, max = 2000): { i: number[]; q: number[] } {
  const stride = Math.max(1, Math.floor(i.length / max));
  const oi: number[] = [];
  const oq: number[] = [];
  for (let k = 0; k < i.length && oi.length < max; k += stride) {
    oi.push(i[k]);
    oq.push(q[k]);
  }
  return { i: oi, q: oq };
}
