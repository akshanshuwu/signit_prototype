"""Demo store — frozen contract mirror of prototype lib/demo.ts.

Offline fallback + smoke seed only (F1+): the 4 precomputed JSONs bundled
in assets/demo/ are NOT the primary path. Normal flow is live:
ingest/synth -> engine chain -> to_demo_dict. Use load_demo() only for
explicit fallback when the live chain cannot produce a view, and
validate_demo() as the contract checker (also used by intel_pdf).
Works both in dev and inside a PyInstaller bundle (sys._MEIPASS).
"""
from __future__ import annotations

import json
import os
import sys

DEMO_IDS = ("bpsk", "qpsk", "qam16", "fsk2")

SAMPLE_META = {
    "bpsk": ("BPSK", "Binary PSK · 2k sym/s · fs 48k"),
    "qpsk": ("QPSK", "Quadrature PSK · 2k sym/s · fs 48k"),
    "qam16": ("16QAM", "16-point QAM · 2k sym/s · fs 48k"),
    "fsk2": ("2FSK", "Binary FSK · dev 2 kHz · fs 48k"),
}

_REQUIRED = {
    "meta": ("modulation", "fs", "symbol_rate", "snr_db", "center_freq", "file"),
    "predictions": ("modulation", "confidence", "votes", "fs_est", "symbol_rate_est", "bw_est", "snr_est"),
    "psd": ("freqs", "mags_db"),
    "spectrogram": ("times", "freqs", "z_db"),
    "constellation": ("i", "q"),
    "bits_preview": ("hex", "ascii", "corr_peak"),
    "comparator": ("iq_snr", "wav_snr", "note"),
}


def resource_path(*parts: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, *parts)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), *parts)


def demo_path(demo_id: str) -> str:
    return resource_path("assets", "demo", f"{demo_id}.json")


def load_demo(demo_id: str) -> dict:
    """Load a bundled demo JSON. Raises ValueError for unknown ids, FileNotFoundError if missing."""
    if demo_id not in DEMO_IDS:
        raise ValueError(f'Unknown capture "{demo_id}". Open one of bpsk / qpsk / qam16 / fsk2.')
    path = demo_path(demo_id)
    with open(path, "r") as f:
        return json.load(f)


def validate_demo(demo: dict) -> list[str]:
    """Return a list of contract violations (empty = valid). Mirrors lib/demo.ts shape."""
    errs: list[str] = []
    for section, fields in _REQUIRED.items():
        if section not in demo:
            errs.append(f"missing section: {section}")
            continue
        for field in fields:
            if field not in demo[section]:
                errs.append(f"missing field: {section}.{field}")
    if errs:
        return errs
    if not (len(demo["psd"]["freqs"]) == len(demo["psd"]["mags_db"]) == 512):
        errs.append("psd must be 512 pts")
    spec = demo["spectrogram"]
    if not (len(spec["freqs"]) == 128 and len(spec["times"]) == 64):
        errs.append("spectrogram axes must be 128 freq x 64 time")
    if not (len(spec["z_db"]) == 128 and len(spec["z_db"][0]) == 64):
        errs.append("spectrogram z must be 128x64")
    const = demo["constellation"]
    if not (len(const["i"]) <= 2000 and len(const["q"]) <= 2000):
        errs.append("constellation must be <=2000 pts")
    cp = demo["bits_preview"]["corr_peak"]
    for key in ("lag", "value", "lags", "vals"):
        if key not in cp:
            errs.append(f"missing field: bits_preview.corr_peak.{key}")
    return errs


def format_khz(hz: float) -> str:
    return f"{hz / 1000:.1f} kHz"
