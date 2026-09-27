// Playback helpers: turn decoded IQData into listenable mono audio.
// Analysis arrays are never mutated — playback is a listen-only copy.
// .wav: channel-0 PCM directly. .iq/.bin: RF sonification (I-channel
// normalized), labelled as such in the UI — it sounds like noise and
// must not be mistaken for demodulated audio.

import type { IQData } from "./parse";

export interface PlaybackData {
  /** Mono samples for listening only (copy, safe to resample). */
  mono: Float32Array;
  /** Capture sample rate — AudioBuffer duration = mono.length / sampleRate. */
  sampleRate: number;
  /** True when the audio is sonified RF rather than real recorded audio. */
  sonified: boolean;
}

export function toPlaybackMono(iq: IQData): PlaybackData {
  if (iq.kind === "wav") {
    return { mono: new Float32Array(iq.i), sampleRate: iq.fs, sonified: false };
  }
  // Sonify complex capture via I-channel, peak-normalized to 0.9.
  const n = iq.i.length;
  const mono = new Float32Array(n);
  let peak = 0;
  for (let k = 0; k < n; k++) {
    const a = Math.abs(iq.i[k]);
    if (a > peak) peak = a;
  }
  const g = peak > 1e-6 ? 0.9 / peak : 1;
  for (let k = 0; k < n; k++) mono[k] = iq.i[k] * g;
  return { mono, sampleRate: iq.fs, sonified: true };
}

export function makeAudioBuffer(
  ctx: AudioContext,
  data: PlaybackData
): AudioBuffer {
  const buf = ctx.createBuffer(1, data.mono.length, data.sampleRate);
  buf.copyToChannel(data.mono, 0);
  return buf;
}

/** RMS peaks per bin for the waveform overview (default 2000 bins). */
export function computePeaks(mono: Float32Array, bins = 2000): Float32Array {
  const n = Math.max(1, Math.min(bins, mono.length));
  const peaks = new Float32Array(n);
  const per = mono.length / n;
  for (let b = 0; b < n; b++) {
    const s = Math.floor(b * per);
    const e = Math.max(s + 1, Math.floor((b + 1) * per));
    let sum = 0;
    for (let k = s; k < e && k < mono.length; k++) sum += mono[k] * mono[k];
    peaks[b] = Math.sqrt(sum / (e - s));
  }
  // Normalize so the overview fills the lane.
  let peak = 0;
  for (let b = 0; b < n; b++) if (peaks[b] > peak) peak = peaks[b];
  if (peak > 1e-6) {
    const g = 1 / peak;
    for (let b = 0; b < n; b++) peaks[b] *= g;
  }
  return peaks;
}

export function formatTime(sec: number): string {
  if (!isFinite(sec) || sec < 0) sec = 0;
  const m = Math.floor(sec / 60);
  const s = sec - m * 60;
  return `${m}:${s < 10 ? "0" : ""}${s.toFixed(1)}`;
}
