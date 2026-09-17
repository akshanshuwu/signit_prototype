// Bits preview: sign-slice + hex/ascii + autocorr peak.

export interface CorrPeak {
  lag: number;
  value: number;
  lags: number[];
  vals: number[];
}

function autocorr(bits: number[], maxLag = 256): CorrPeak {
  const L = Math.min(maxLag, Math.floor(bits.length / 2));
  const lags: number[] = [];
  const vals: number[] = [];
  const mean = bits.reduce((a, b) => a + b, 0) / bits.length;
  let denom = 0;
  for (const b of bits) denom += (b - mean) * (b - mean);
  let bestLag = 0;
  let bestVal = -1;
  for (let lag = 0; lag < L; lag++) {
    let num = 0;
    for (let k = 0; k + lag < bits.length; k++) num += (bits[k] - mean) * (bits[k + lag] - mean);
    const v = denom > 0 ? num / denom : 0;
    lags.push(lag);
    vals.push(v);
    if (lag > 4 && v > bestVal) {
      bestVal = v;
      bestLag = lag;
    }
  }
  return { lag: bestLag, value: bestVal < 0 ? 0 : bestVal, lags, vals };
}

export function bitsPreview(i: Float32Array, q: Float32Array, mod: string): { hex: string; ascii: string; corr_peak: CorrPeak } {
  const n = Math.min(i.length, 8192);
  const bits: number[] = new Array(n);
  if (mod === "2FSK") {
    // FM-demod sign
    for (let k = 0; k < n; k++) {
      const k2 = Math.min(i.length - 1, k + 1);
      const fm = q[k2] * i[k] - q[k] * i[k2];
      bits[k] = fm >= 0 ? 1 : 0;
    }
  } else {
    for (let k = 0; k < n; k++) bits[k] = i[k] >= 0 ? 1 : 0;
  }
  const nBytes = 32;
  const bytes: number[] = [];
  for (let b = 0; b < nBytes; b++) {
    let v = 0;
    for (let k = 0; k < 8; k++) v = (v << 1) | (bits[b * 8 + k] ?? 0);
    bytes.push(v);
  }
  const hex = bytes.map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
  const ascii = bytes.map((b) => (b >= 32 && b <= 126 ? String.fromCharCode(b) : ".")).join("");
  const corr_peak = autocorr(bits, 256);
  return { hex, ascii, corr_peak };
}
