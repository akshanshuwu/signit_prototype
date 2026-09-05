"""Deterministic synthetic bursts — Phase 5 sklearn training set (and only that).

Small rectangular-pulse captures across modulations x SNRs x seeds with a
fixed seed schedule, so the lazily-trained RandomForest is bit-identical
on every machine. Runtime DSP under test uses these too (via engine +
ml code paths, never by copying statistics).
"""
from __future__ import annotations

import numpy as np

from ml.cumulants import CLASSES

FS = 48000
RATE = 2000
SPS = FS // RATE
N_SYM = 400  # short bursts: training throughput over realism (test set differs)

TRAIN_SNRS = (5.0, 12.0, 20.0)
TRAIN_SEEDS = (100, 101)

_QAM_LEVELS = np.array([-3.0, -1.0, 1.0, 3.0]) / np.sqrt(10.0)


def _channel(x: np.ndarray, snr_db: float, freq_offset: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    sig_pwr = float(np.mean(np.abs(x) ** 2))
    noise_pwr = sig_pwr / (10.0 ** (snr_db / 10.0))
    noise = (rng.standard_normal(len(x)) + 1j * rng.standard_normal(len(x)))
    noise = noise * np.sqrt(noise_pwr / 2.0)
    t = np.arange(len(x), dtype=np.float64) / FS
    return ((x + noise) * np.exp(2j * np.pi * freq_offset * t)).astype(np.complex64)


def synth(mod: str, snr_db: float, seed: int, n_sym: int = N_SYM) -> np.ndarray:
    """One synthetic burst. Raises ValueError on unknown mod."""
    rng = np.random.default_rng(seed)
    if mod == "BPSK":
        bits = rng.integers(0, 2, n_sym)
        sym = np.where(bits, 1.0, -1.0).astype(np.complex64)
        x = np.repeat(sym, SPS)
    elif mod == "QPSK":
        bits = rng.integers(0, 2, 2 * n_sym).astype(np.int16)
        i = 2 * bits[0::2] - 1
        q = 2 * bits[1::2] - 1
        x = np.repeat(((i + 1j * q) / np.sqrt(2.0)).astype(np.complex64), SPS)
    elif mod == "16QAM":
        bits = rng.integers(0, 2, 4 * n_sym).astype(np.int16)
        ri = bits[0::4] * 2 + bits[1::4]
        qi = bits[2::4] * 2 + bits[3::4]
        x = np.repeat((_QAM_LEVELS[ri] + 1j * _QAM_LEVELS[qi]).astype(np.complex64), SPS)
    elif mod == "2FSK":
        # NOTE: dev 1500 != baud 2000 on purpose. dev == baud aliases the
        # 1-sps phases (steps of exactly +-2pi) into a frozen phasor that
        # no symbol-rate statistic can separate from BPSK; real captures
        # rarely sit on that integer degeneracy (demod's sample-rate FM
        # path covers it when they do).
        bits = rng.integers(0, 2, n_sym)
        freqs = np.where(bits, 1500.0, -1500.0)
        phase = 2.0 * np.pi * np.cumsum(np.repeat(freqs, SPS)) / FS
        x = np.exp(1j * phase).astype(np.complex64)
    else:
        raise ValueError(f"unknown mod {mod}")
    return _channel(x, snr_db, 200.0, seed)


def training_set() -> tuple[list[np.ndarray], list[str]]:
    """Deterministic (bursts, labels). 4 mods x 3 SNRs x 2 seeds = 24 bursts."""
    xs, ys = [], []
    for mod in CLASSES:
        for snr in TRAIN_SNRS:
            for k, seed in enumerate(TRAIN_SEEDS):
                xs.append(synth(mod, snr, seed * 1000 + hash(mod) % 997 + k))
                ys.append(mod)
    return xs, ys
