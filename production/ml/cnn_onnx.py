"""CNN vote via ONNX Runtime.

Contract (frozen for the training phase):
  input:  (1, 1, 64, 64) float32 constellation-density image, values in [0, 1]
  output: (1, 4) logits over ("BPSK", "QPSK", "16QAM", "2FSK")
  file:   ml/models/signit_cnn.onnx (repo-excluded until trained)

Image source matters: raw bursts carry carrier offset, so rasterizing raw
samples smears clusters into rings. preview_image() therefore
carrier-corrects (centroid + M=4 fine, same as the demod chain) and snaps
to symbol centers via timing search BEFORE rasterizing; train and infer
share this path by construction, with a raw-sample fallback when rate or
timing recovery fails (short/weak previews).

Without a model file (or without onnxruntime installed) the vote is
"pending" with no weight — the ensemble never waits on it. A lone
uncorroborated CNN vote also abstains (see ml.ensemble.combine). Use
ml/train_cnn.py to produce the model.
"""
from __future__ import annotations

import os

import numpy as np

CLASSES = ("BPSK", "QPSK", "16QAM", "2FSK")
IMG = 64


def model_path() -> str:
    # Frozen exe: model is bundled as ml/models/signit_cnn.onnx under _MEIPASS
    # (see signit.spec model_datas). Dev: ml/models/ next to this file.
    try:
        from app.demo_store import resource_path
        bundled = resource_path("ml", "models", "signit_cnn.onnx")
        if os.path.isfile(bundled):
            return bundled
    except Exception:
        pass
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "signit_cnn.onnx")


def _density(y: np.ndarray, size: int = IMG) -> np.ndarray:
    """64x64 density image of complex points, values in [0, 1]."""
    y = np.asarray(y, dtype=np.complex64).ravel()
    if y.size == 0:
        return np.zeros((1, 1, size, size), dtype=np.float32)
    mag = float(np.max(np.abs(y)))
    if mag <= 0:
        return np.zeros((1, 1, size, size), dtype=np.float32)
    yn = y / mag * 0.95  # into [-1, 1]
    ix = np.clip(((yn.real + 1.0) / 2.0 * size).astype(int), 0, size - 1)
    iy = np.clip(((yn.imag + 1.0) / 2.0 * size).astype(int), 0, size - 1)
    img = np.zeros((size, size), dtype=np.float32)
    np.add.at(img, (iy, ix), 1.0)
    img /= max(img.max(), 1e-9)
    return img.reshape(1, 1, size, size)


def constellation_image(x: np.ndarray, size: int = IMG, n: int = 4096) -> np.ndarray:
    """Density image of raw complex samples (fallback path; see preview_image)."""
    y = np.asarray(x, dtype=np.complex64).ravel()[:n]
    return _density(y, size)


def symbols_for_image(preview: np.ndarray, fs: int, n: int = 4096):
    """Carrier-corrected, timing-snapped symbol centers for imaging.

    Returns (symbols, note). Raises ValueError when rate/timing recovery
    fails so the caller can fall back to raw samples.
    """
    from engine.demod import (
        _phase_track,
        _to_2sps,
        derotate,
        estimate_carrier,
        estimate_symbol_rate,
        mix_down,
        refine_freq,
        timing_search,
    )

    x = np.asarray(preview, dtype=np.complex64).ravel()
    if x.size == 0 or not fs or fs <= 0:
        raise ValueError("empty preview or bad fs")
    coarse = estimate_carrier(x, fs)
    x_bb = mix_down(x, fs, coarse)
    if len(x_bb) >= 64:
        fine = estimate_carrier(x_bb**4, fs) / 4.0
        if abs(fine) <= fs / 4.0:  # M=4 alias guard (FSK/wideband can alias)
            x_bb = mix_down(x_bb, fs, fine)
    rate, _method = estimate_symbol_rate(x_bb, fs)
    if rate <= 0:
        raise ValueError("no symbol-rate line")
    sps = float(fs) / float(rate)
    sym, _tau = timing_search(_to_2sps(x_bb, sps))
    # Stop residual spin so clusters (not rings) reach the rasterizer:
    # M=4 strips BPSK/QPSK/16QAM (BPSK^4 == 1), FSK keeps its ring shape.
    sym = _phase_track(derotate(sym, sps, fs, refine_freq(sym, sps, fs, 4)), 4)
    sym = np.asarray(sym).ravel()[:n]
    if sym.size < 64:
        raise ValueError(f"only {sym.size} symbols")
    return sym.astype(np.complex64), f"carrier+timing corrected ({len(sym)} sym)"


def preview_image(preview: np.ndarray, fs: int, size: int = IMG, n: int = 4096):
    """Shared train/infer image path. Returns (img, note)."""
    try:
        sym, note = symbols_for_image(preview, fs, n)
        return _density(sym, size), note
    except Exception as exc:
        return constellation_image(preview, size, n), f"raw fallback ({exc})"


def cnn_vote(preview: np.ndarray, fs: int) -> dict:
    """Vote dict {modulation, confidence, note}. Never raises."""
    path = model_path()
    if not os.path.isfile(path):
        return {
            "modulation": "pending", "confidence": 0.0,
            "note": "signit_cnn.onnx not trained yet (Phase 6)",
        }
    try:
        import onnxruntime as ort
    except ImportError:
        return {
            "modulation": "pending", "confidence": 0.0,
            "note": "onnxruntime not installed — cnn abstains",
        }
    try:
        sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        img, _note = preview_image(preview, fs)
        logits = np.asarray(sess.run(None, {sess.get_inputs()[0].name: img})[0]).ravel()
        ex = np.exp(logits - logits.max())
        proba = ex / ex.sum()
        best = int(np.argmax(proba))
        return {
            "modulation": str(CLASSES[best]) if best < len(CLASSES) else "UNKNOWN",
            "confidence": float(proba[best]),
            "note": f"onnx {os.path.basename(path)}",
        }
    except Exception as exc:
        return {"modulation": "pending", "confidence": 0.0, "note": f"cnn infer failed: {exc}"}
