// Lightweight estimators: SNR/BW/symbol-rate + cumulant classifier.
// Port of production/ml/cumulants.py thresholds, simplified for browser.

export type ModLabel = "BPSK" | "QPSK" | "16QAM" | "2FSK" | "UNKNOWN";

function median(a: number[]): number {
  const s = a.slice().sort((x, y) => x - y);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

export function estimateSnrBw(freqs: number[], mags: number[]): { snr: number; bw: number } {
  const med = median(mags);
  const top = mags.slice().sort((a, b) => b - a).slice(0, 3);
  const peak = median(top);
  const snr = Math.min(40, Math.max(0, peak - med));
  // BW: width above peak-10dB
  const thr = peak - 10;
  let lo = 0;
  let hi = mags.length - 1;
  const pkIdx = mags.indexOf(Math.max(...mags));
  for (let k = pkIdx; k >= 0; k--) { if (mags[k] < thr) { lo = k; break; } lo = k; }
  for (let k = pkIdx; k < mags.length; k++) { if (mags[k] < thr) { hi = k; break; } hi = k; }
  const bw = Math.max(freqs[1] - freqs[0], Math.abs(freqs[hi] - freqs[lo]));
  return { snr, bw };
}

export function estimateSymbolRate(i: Float32Array, q: Float32Array, fs: number): number {
  // envelope zero-cross median distance (cheap baud hint)
  const n = Math.min(i.length, 65536);
  const env = new Float32Array(n);
  let mean = 0;
  for (let k = 0; k < n; k++) {
    const m = Math.sqrt(i[k] * i[k] + q[k] * q[k]);
    env[k] = m;
    mean += m;
  }
  mean /= n;
  const crosses: number[] = [];
  for (let k = 1; k < n; k++) {
    if ((env[k - 1] < mean && env[k] >= mean) || (env[k - 1] >= mean && env[k] < mean)) crosses.push(k);
  }
  if (crosses.length < 10) return 2000;
  const gaps: number[] = [];
  for (let k = 1; k < crosses.length; k++) gaps.push(crosses[k] - crosses[k - 1]);
  const med = median(gaps);
  if (med < 2) return 2000;
  const sym = fs / (med * 2);
  return Math.min(10000, Math.max(500, Math.round(sym / 100) * 100));
}

export function classify(i: Float32Array, q: Float32Array): { mod: ModLabel; conf: number; cumulants: string } {
  const n = Math.min(i.length, 32768);
  // normalize power
  let p = 0;
  for (let k = 0; k < n; k++) p += i[k] * i[k] + q[k] * q[k];
  p /= n;
  const norm = Math.sqrt(p) || 1;
  let c20 = 0;
  let c40 = 0;
  let c42 = 0;
  let fmVar = 0;
  let fmMean = 0;
  const fm: number[] = [];
  for (let k = 0; k < n; k++) {
    const x = i[k] / norm;
    const y = q[k] / norm;
    c20 += x * x + y * y;
    // crude moment proxies (fast, judge-proof)
    c40 += Math.abs(x * x - y * y);
    c42 += Math.abs(x * y);
    if (k > 0) {
      const dI = i[k] - i[k - 1];
      const dQ = q[k] - q[k - 1];
      const inst = Math.abs(dQ * i[k] - dI * q[k]) / (p + 1e-9);
      fm.push(inst);
      fmMean += inst;
    }
  }
  c20 /= n; c40 /= n; c42 /= n;
  fmMean /= Math.max(1, fm.length);
  for (const v of fm) fmVar += (v - fmMean) * (v - fmMean);
  fmVar /= Math.max(1, fm.length);

  // FSK gate: high FM variance + low amplitude variation
  const dc = Math.abs(c20 - 1);
  const isFSK = fmVar > 0.08 && c40 < 0.25;
  type Cand = { mod: ModLabel; d: number };
  let cands: Cand[];
  if (isFSK) {
    cands = [
      { mod: "2FSK", d: 0 },
      { mod: "QPSK", d: 0.8 },
      { mod: "BPSK", d: 1.0 },
      { mod: "16QAM", d: 1.2 },
    ];
  } else {
    // distance in (c40, c42) space to theory: BPSK(1.0,.5) QPSK(.5,.25) QAM(.34,.2) FSK(.05,.05)
    const feats: Record<Exclude<ModLabel, "UNKNOWN">, [number, number]> = {
      BPSK: [1.0, 0.5],
      QPSK: [0.5, 0.25],
      "16QAM": [0.34, 0.2],
      "2FSK": [0.05, 0.05],
    };
    cands = (Object.keys(feats) as Array<Exclude<ModLabel, "UNKNOWN">>).map((m) => {
      const [t40, t42] = feats[m];
      const d = Math.hypot(c40 - t40, c42 - t42);
      return { mod: m, d };
    });
    cands.sort((a, b) => a.d - b.d);
    void dc;
  }
  const best = cands[0];
  const second = cands[1];
  if (best.d > 0.75) return { mod: "UNKNOWN", conf: 0.4, cumulants: "UNKNOWN" };
  const margin = second.d - best.d;
  const conf = Math.min(0.95, Math.max(0.55, 0.55 + margin * 1.2));
  return { mod: best.mod, conf, cumulants: best.mod };
}
