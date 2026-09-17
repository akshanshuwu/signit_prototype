// Result contract for real-file analysis (produced in-browser by lib/dsp/toDemo.ts).
// Shape frozen: all plots + ReportCard depend on this.
export interface DemoJson {
  meta: { modulation: string; fs: number; symbol_rate: number; snr_db: number; center_freq: number; file: string };
  predictions: {
    modulation: string;
    confidence: number;
    votes: { CNN: number; cumulants: string };
    fs_est: number;
    symbol_rate_est: number;
    bw_est: number;
    snr_est: number;
  };
  psd: { freqs: number[]; mags_db: number[] };
  spectrogram: { times: number[]; freqs: number[]; z_db: number[][] };
  constellation: { i: number[]; q: number[] };
  bits_preview: { hex: string; ascii: string; corr_peak: { lag: number; value: number; lags: number[]; vals: number[] } };
  comparator: { iq_snr: number; wav_snr: number; note: string };
  log: string[];
}

export function formatKhz(hz: number): string {
  return `${(hz / 1000).toFixed(1)} kHz`;
}
