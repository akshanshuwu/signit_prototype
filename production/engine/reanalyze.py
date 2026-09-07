"""Re-analysis helpers — Phase 7 (ROI slices + impairment probes).

Pure NumPy over an ingest preview: slice a time window for Waterfall-ROI
re-analysis, or degrade a copy (AWGN / frequency offset) to probe how the
chain degrades. The caller re-runs the standard chain
(estimators → demod → vote → fec) on the result — same code path as
ingest, so ROI/impairment views are directly comparable.
"""
from __future__ import annotations

import numpy as np


def slice_preview(preview: np.ndarray, fs: int, t0_s: float, t1_s: float) -> np.ndarray:
    """Time-window slice [t0_s, t1_s). Clamps to bounds; raises on empty."""
    x = np.asarray(preview, dtype=np.complex64).ravel()
    if x.size == 0:
        raise ValueError("empty preview — nothing to slice")
    if not fs or fs <= 0:
        raise ValueError(f"bad sample rate fs={fs}")
    dur = len(x) / float(fs)
    a = max(0, int(float(t0_s) * fs))
    b = min(len(x), int(float(t1_s) * fs))
    if b - a < 64:
        raise ValueError(
            f"slice [{t0_s:.2f}s, {t1_s:.2f}s) too short on a {dur:.2f}s capture "
            f"({b - a} samples) — need >= 64"
        )
    return x[a:b].astype(np.complex64)


def add_awgn(preview: np.ndarray, snr_db: float, seed: int = 7) -> np.ndarray:
    """Copy degraded to target in-band SNR (dB). Deterministic given seed."""
    x = np.asarray(preview, dtype=np.complex64)
    sig_pwr = float(np.mean(np.abs(x) ** 2))
    if sig_pwr <= 0:
        raise ValueError("zero-power preview — cannot set SNR")
    rng = np.random.default_rng(seed)
    noise = (rng.standard_normal(x.shape) + 1j * rng.standard_normal(x.shape))
    noise = noise * np.sqrt(sig_pwr / (10.0 ** (float(snr_db) / 10.0)) / 2.0)
    return (x + noise).astype(np.complex64)


def add_freq_offset(preview: np.ndarray, fs: int, offset_hz: float) -> np.ndarray:
    """Copy rotated by offset_hz (carrier-stress probe)."""
    x = np.asarray(preview, dtype=np.complex64).ravel()
    if offset_hz == 0.0:
        return x.copy()
    t = np.arange(len(x), dtype=np.float64) / float(fs)
    return (x.astype(np.complex128) * np.exp(2j * np.pi * float(offset_hz) * t)).astype(np.complex64)


def slice_duration_s(preview: np.ndarray, fs: int) -> float:
    return len(np.asarray(preview).ravel()) / float(fs)
