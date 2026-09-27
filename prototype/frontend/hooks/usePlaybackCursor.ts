"use client";

import { useEffect, useState } from "react";

/**
 * Playback cursor sampled at ~10Hz for Plotly overlays.
 * Returns null when inactive so overlays hide. Canvas components
 * should read getTime() directly instead (no React render per frame).
 */
export function usePlaybackCursor(
  getTime: () => number,
  playing: boolean,
  active: boolean
): number | null {
  const [t, setT] = useState<number | null>(null);

  useEffect(() => {
    if (!active) {
      setT(null);
      return;
    }
    setT(getTime());
    if (!playing) return;
    const id = setInterval(() => setT(getTime()), 100);
    return () => clearInterval(id);
  }, [getTime, playing, active]);

  return t;
}
