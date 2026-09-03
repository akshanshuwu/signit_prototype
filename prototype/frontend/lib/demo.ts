// Frozen contract for v1 demo JSONs. Do not change shape without updating generator + all plots.
export type DemoId = "bpsk" | "qpsk" | "qam16" | "fsk2";

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

export const DEMO_IDS: DemoId[] = ["bpsk", "qpsk", "qam16", "fsk2"];

export async function loadDemo(id: DemoId): Promise<DemoJson> {
  // v1: local static only for PPT reliability. v2 may try backend first.
  const res = await fetch(`/demo/${id}.json`, { cache: "no-store" });
  if (!res.ok) throw new Error(`demo ${id} not found`);
  return (await res.json()) as DemoJson;
}

export function formatKhz(hz: number): string {
  return `${(hz / 1000).toFixed(1)} kHz`;
}
