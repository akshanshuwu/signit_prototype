"use client";

import type { PlaybackSync } from "../hooks/usePlaybackSync";
import { formatTime } from "../lib/dsp/playback";

/** Transport bar: Play/Pause, seek timeline, time labels, volume. */
export default function AudioPlayer({
  sync,
  fileName,
  sonified,
}: {
  sync: PlaybackSync;
  fileName: string;
  sonified: boolean;
}) {
  const { status, currentTime, duration, volume, muted } = sync;
  const playing = status === "playing";

  return (
    <div className="min-w-0 rounded-md border border-line bg-white p-3 shadow-subtle">
      <div className="flex min-w-0 flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={sync.toggle}
          disabled={status === "idle"}
          aria-label={playing ? "Pause" : "Play"}
          className="btn-primary flex h-9 w-9 shrink-0 items-center justify-center disabled:opacity-40"
        >
          {playing ? (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
              <rect x="2.5" y="2" width="3.2" height="10" rx="0.8" />
              <rect x="8.3" y="2" width="3.2" height="10" rx="0.8" />
            </svg>
          ) : (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
              <path d="M4 2.3v9.4c0 .8.9 1.3 1.6.9l7-4.7c.6-.4.6-1.4 0-1.8l-7-4.7c-.7-.4-1.6.1-1.6.9z" />
            </svg>
          )}
        </button>

        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 items-baseline justify-between gap-2">
            <p className="truncate font-mono text-[12px] font-bold text-paper">{fileName}</p>
            <p className="shrink-0 font-mono text-[11px] tabular-nums text-fog">
              {formatTime(currentTime)} / {formatTime(duration)}
            </p>
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(0.01, duration)}
            step={0.01}
            value={Math.min(currentTime, Math.max(0.01, duration))}
            onChange={(e) => sync.seek(Number(e.target.value))}
            aria-label="Seek"
            className="mt-1 w-full accent-[#0E7C6B]"
          />
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={sync.toggleMute}
            aria-label={muted ? "Unmute" : "Mute"}
            className="rounded-md border border-line px-2 py-1 font-mono text-[11px] text-fog hover:border-signal hover:text-paper"
          >
            {muted ? "MUTE·OFF" : "MUTE"}
          </button>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={muted ? 0 : volume}
            onChange={(e) => sync.setVolume(Number(e.target.value))}
            aria-label="Volume"
            className="w-20 accent-[#0E7C6B]"
          />
        </div>
      </div>
      {sonified && (
        <p className="mt-2 font-mono text-[11px] leading-relaxed text-fog">
          RF SONIFICATION — I-channel normalized for listening. Sounds like noise; analysis is unaffected.
        </p>
      )}
    </div>
  );
}
