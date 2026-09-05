"""Estimators — Phase 3.

Real signal measurements computed from an IngestResult.preview
(complex64, bounded to PREVIEW_N). Pure NumPy + SciPy (pyFFTW/Numba
acceleration lands in a later hardening pass; API stays stable).

Outputs mirror the frozen demo contract shapes so the existing
ResultsTabs/ReportCard render without modification:
- PSD: 512 pts (freqs Hz centered, mags dB)
- Spectrogram: 128 freq x 64 time (z dB)
- Constellation: <=2000 pts (I/Q)
- Corr peak: 256 lags
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np

PSD_N = 512
SPEC_FREQ = 128
SPEC_TIME = 64
CONST_MAX = 2000
CORR_N = 256

WELCH_NPERSEG = 4096
SPEC_NPERSEG = 256
SPEC_NOVERLAP = 192


class EstimatorError(ValueError):
    pass


@dataclass
class EstimateResult:
    fs: int
    fc: float
    n_preview: int
    freqs: np.ndarray = field(repr=False)      # (512,) Hz centered
    mags_db: np.ndarray = field(repr=False)    # (512,) dB
    spec_times: np.ndarray = field(repr=False)  # (64,) seconds
    spec_freqs: np.ndarray = field(repr=False)  # (128,) Hz centered
    spec_z_db: np.ndarray = field(repr=False)   # (128, 64) dB
    const_i: np.ndarray = field(repr=False)     # (<=2000,)
    const_q: np.ndarray = field(repr=False)     # (<=2000,)
    snr_db: float = 0.0
    bw_hz: float = 0.0
    peak_freq: float = 0.0
    env_mean: float = 0.0
    corr_lags: np.ndarray = field(repr=False, default_factory=lambda: np.zeros(0))
    corr_vals: np.ndarray = field(repr=False, default_factory=lambda: np.zeros(0))
    corr_lag: int = 0
    corr_value: float = 0.0
    hex_text: str = ""
    ascii_text: str = ""


def _as_complex(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.complex64)
    if arr.ndim != 1:
        arr = arr.ravel()
    if arr.size == 0:
        raise EstimatorError("empty preview — nothing to estimate")
    return arr


def _resample_to(arr: np.ndarray, n: int) -> np.ndarray:
    """Linear resample of 1-D array to exactly n points."""
    arr = np.asarray(arr, dtype=float)
    if len(arr) == n:
        return arr
    if len(arr) < 2:
        return np.full(n, float(arr[0]) if len(arr) else 0.0)
    src = np.linspace(0.0, 1.0, len(arr))
    dst = np.linspace(0.0, 1.0, n)
    return np.interp(dst, src, arr)


def compute_psd(x: np.ndarray, fs: int) -> tuple[np.ndarray, np.ndarray]:
    """Two-sided Welch PSD, resampled to exactly 512 pts. Returns (freqs Hz, mags dB)."""
    from scipy.signal import welch

    x = _as_complex(x)
    nperseg = int(min(WELCH_NPERSEG, max(64, len(x))))
    freqs, pxx = welch(
        x, fs=float(fs), nperseg=nperseg, noverlap=nperseg // 2,
        return_onesided=False, scaling="density", average="mean",
    )
    # Center: fftshift so freqs run -fs/2..fs/2.
    order = np.argsort(freqs)
    freqs, pxx = freqs[order], pxx[order]
    freqs512 = np.linspace(float(-fs) / 2.0, float(fs) / 2.0, PSD_N)
    mags = np.interp(freqs512, freqs, 10.0 * np.log10(pxx + 1e-18))
    return freqs512.astype(float), mags.astype(float)


def compute_spectrogram(x: np.ndarray, fs: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """STFT magnitude spectrogram reduced to 128 freq x 64 time (dB).

    Returns (times_s (64,), freqs_hz (128,), z_db (128, 64)).
    """
    from scipy.signal import spectrogram

    x = _as_complex(x)
    nperseg = int(min(SPEC_NPERSEG, max(64, len(x))))
    noverlap = min(SPEC_NOVERLAP, nperseg - 8)
    freqs, times, sxx = spectrogram(
        x, fs=float(fs), nperseg=nperseg, noverlap=noverlap,
        return_onesided=False, scaling="density", mode="magnitude",
    )
    order = np.argsort(freqs)
    freqs, sxx = freqs[order], sxx[order, :]
    z = 20.0 * np.log10(sxx + 1e-12)  # (n_freq, n_time)

    # Freq axis -> 128 (average adjacent pairs when 256, else interp per column).
    if z.shape[0] >= SPEC_FREQ:
        # Even decimation by averaging blocks.
        block = z.shape[0] // SPEC_FREQ
        trim = block * SPEC_FREQ
        z = z[:trim, :].reshape(SPEC_FREQ, block, z.shape[1]).mean(axis=1)
        f128 = freqs[:trim].reshape(SPEC_FREQ, block).mean(axis=1)
    else:
        f128 = np.linspace(float(freqs[0]), float(freqs[-1]), SPEC_FREQ)
        z = np.vstack([_resample_to(z[:, j], SPEC_FREQ) for j in range(z.shape[1])]).T \
            if z.shape[1] else np.zeros((SPEC_FREQ, 0))

    # Time axis -> 64 evenly spaced frames.
    nt = z.shape[1]
    if nt == 0:
        raise EstimatorError("spectrogram produced no frames")
    if nt >= SPEC_TIME:
        idx = np.linspace(0, nt - 1, SPEC_TIME).astype(int)
        z64 = z[:, idx]
        t64 = times[idx]
    else:
        t64 = np.linspace(float(times[0]), float(times[-1]), SPEC_TIME)
        z64 = np.vstack([_resample_to(z[i, :], SPEC_TIME) for i in range(z.shape[0])])
    return t64.astype(float), f128.astype(float), z64.astype(float)


def constellation_points(x: np.ndarray, max_pts: int = CONST_MAX) -> tuple[np.ndarray, np.ndarray]:
    x = _as_complex(x)
    n = len(x)
    if n <= max_pts:
        idx = np.arange(n)
    else:
        idx = np.linspace(0, n - 1, max_pts).astype(int)
    return np.asarray(x.real[idx], dtype=float), np.asarray(x.imag[idx], dtype=float)


def estimate_snr_bw(freqs: np.ndarray, mags_db: np.ndarray) -> tuple[float, float, float]:
    """Robust SNR + signal BW + peak freq from a 512-pt PSD.

    SNR = mean(top-3 bins) vs median — high for tones, low for flat noise.
    BW = bins within 10 dB of the peak x bin width — narrow for tones,
    wide for noise/wideband. (Integration-based OBW overestimates on
    dB-interpolated PSDs, so threshold width is used for display.)
    """
    mags = np.asarray(mags_db, dtype=float)
    freqs = np.asarray(freqs, dtype=float)
    peak_idx = int(np.argmax(mags))
    peak_freq = float(freqs[peak_idx])
    peak = float(mags[peak_idx])
    bin_hz = abs(float(freqs[1] - freqs[0])) if len(freqs) > 1 else 0.0
    bw = float(np.count_nonzero(mags >= peak - 10.0) * bin_hz)
    # SNR via peak bins vs median (robust, no ground truth needed).
    # A tone concentrates power in a few bins; flat noise does not.
    k = 3
    top = np.partition(mags, -k)[-k:].mean()
    med = float(np.median(mags))
    snr = float(np.clip(top - med, 0.0, 40.0))
    return snr, bw, peak_freq


def envelope_mean(x: np.ndarray) -> float:
    """Mean Hilbert envelope of the real part (bounded to 8k samples)."""
    from scipy.signal import hilbert

    x = _as_complex(x)
    seg = np.asarray(x.real[:8192], dtype=float)
    if seg.size < 16:
        return float(np.mean(np.abs(seg))) if seg.size else 0.0
    analytic = hilbert(seg)
    return float(np.mean(np.abs(analytic)))


def bits_preview(x: np.ndarray) -> tuple[str, str, np.ndarray, np.ndarray, int, float]:
    """Hard-slice sign(I)/sign(Q) -> packed bytes -> hex/ascii + autocorr peak.

    Returns (hex_text, ascii_text, lags(256,), vals(256,), peak_lag, peak_val).
    """
    x = _as_complex(x)
    bits_i = (np.asarray(x.real) >= 0).astype(np.uint8)
    bits_q = (np.asarray(x.imag) >= 0).astype(np.uint8)
    bits = np.empty(bits_i.size + bits_q.size, dtype=np.uint8)
    bits[0::2] = bits_i
    bits[1::2] = bits_q
    # Pack MSB-first into bytes; show first 32 bytes like the web BitsView.
    nbytes = min(32, len(bits) // 8)
    raw = np.packbits(bits[: nbytes * 8]).tobytes() if nbytes else b""
    hex_text = " ".join(f"{b:02X}" for b in raw) if raw else "(no bits)"
    ascii_text = "".join(chr(b) if 32 <= b < 127 else "." for b in raw) if raw else "(no bits)"
    # Autocorrelation of +/-1 stream over first 4096 bits, 256 lags.
    stream = (bits[:4096].astype(float) * 2.0 - 1.0) if len(bits) >= 16 else np.array([1.0, -1.0])
    full = np.correlate(stream, stream, mode="full")
    mid = len(full) // 2
    vals = full[mid: mid + CORR_N]
    norm = vals[0] if vals[0] != 0 else 1.0
    vals = vals / norm
    lags = np.arange(len(vals))
    if len(vals) > 2:
        peak = int(np.argmax(vals[1:]) + 1)
    else:
        peak = 0
    return hex_text, ascii_text, lags.astype(int), vals.astype(float), peak, float(vals[peak])


def analyze_preview(preview: np.ndarray, fs: int, fc: float = 0.0) -> EstimateResult:
    """Run all Phase-3 estimators on one ingest preview."""
    if not fs or fs <= 0:
        raise EstimatorError(f"bad sample rate fs={fs}")
    x = _as_complex(preview)
    freqs, mags = compute_psd(x, fs)
    times, s_freqs, z = compute_spectrogram(x, fs)
    ci, cq = constellation_points(x)
    snr, bw, peak = estimate_snr_bw(freqs, mags)
    env = envelope_mean(x)
    hex_t, ascii_t, lags, vals, plag, pval = bits_preview(x)
    return EstimateResult(
        fs=int(fs), fc=float(fc), n_preview=len(x),
        freqs=freqs, mags_db=mags, spec_times=times, spec_freqs=s_freqs,
        spec_z_db=z, const_i=ci, const_q=cq, snr_db=snr, bw_hz=bw,
        peak_freq=peak, env_mean=env, corr_lags=lags, corr_vals=vals,
        corr_lag=plag, corr_value=pval, hex_text=hex_t, ascii_text=ascii_t,
    )


def estimator_log_lines(est: EstimateResult) -> list[str]:
    return [
        f"psd ok: peak {est.peak_freq / 1000.0:.2f} kHz, bw {est.bw_hz / 1000.0:.2f} kHz",
        f"snr est {est.snr_db:.1f} dB from {est.n_preview} preview samples",
        f"spectrogram ok: {est.spec_z_db.shape[0]}x{est.spec_z_db.shape[1]}, "
        f"constellation {len(est.const_i)} pts",
    ]


def to_demo_dict(est: EstimateResult, ingest, kind_note: str = "", demod=None, vote=None, fec=None) -> dict:
    """Convert ingest + estimate (+ Phase-4 demod, + Phase-5 ML vote) into the demo contract.

    Without demod, modulation/classifier fields stay honestly pending.
    With a credible demod, predictions carry the demod guess + margin-based
    confidence and the Bits tab shows demodulated bits + sync correlation.
    With an ML vote, the ensemble winner (which may override the demod,
    flagged in the note) sets modulation + confidence and all voter
    cells are filled (CNN stays 0.0/pending until its model is trained).
    """
    from engine.ingest import IngestResult  # local import: avoid cycle

    assert isinstance(ingest, IngestResult)
    base = os.path.basename(ingest.path)
    wav_snr = est.snr_db if ingest.kind == "wav" else max(0.0, est.snr_db - 5.5)
    demod_ok = demod is not None and getattr(demod, "modulation", "UNKNOWN") != "UNKNOWN"
    vote_ok = vote is not None and getattr(vote, "winner", "UNKNOWN") != "UNKNOWN"
    demod_conf = round(float(min(0.95, max(0.05, demod.margin_db / 12.0))), 2) if demod_ok else 0.0
    if vote_ok:
        modulation = vote.winner
        confidence = round(float(vote.confidence), 2)
        symbol_rate = int(round(demod.symbol_rate)) if demod_ok else 0
        cum_txt = "pending"
        for v in ("cumulants", "sklearn", "cnn"):
            if v in vote.parts:
                cum_txt = f"{vote.parts[v][0]} {vote.parts[v][1]:.2f}"
                if v == "cumulants":
                    break
        votes = {
            "CNN": round(float(vote.parts.get("cnn", ("pending", 0.0))[1]), 2),
            "cumulants": cum_txt,
            "demod": demod_conf,
            "ensemble": confidence,
        }
    elif demod_ok:
        modulation = demod.modulation
        confidence = demod_conf
        symbol_rate = int(round(demod.symbol_rate))
        votes = {"CNN": 0.0, "cumulants": "pending", "demod": confidence}
    else:
        modulation, confidence, symbol_rate = "UNKNOWN", 0.0, 0
        votes = {"CNN": 0.0, "cumulants": "pending"}
    if demod_ok:
        bits_hex, bits_ascii = demod.hex_text, demod.ascii_text
        corr = {
            "lag": int(demod.sync_lag),
            "value": float(demod.sync_value),
            "lags": [int(v) for v in demod.corr_lags],
            "vals": [float(v) for v in demod.corr_vals],
        }
        fec_clean = fec is not None and getattr(fec, "status", "NONE") == "CLEAN"
        if fec_clean:  # decoded payload replaces raw sliced bits in the Bits tab
            bits_hex, bits_ascii = fec.hex_text, fec.ascii_text
        if vote_ok and vote.winner != demod.modulation:
            note = kind_note or (
                f"ensemble {vote.winner} overrides demod {demod.modulation} "
                f"({vote.note}); CNN model pending"
            )
        elif vote_ok:
            note = kind_note or (
                f"ensemble {vote.winner} @ {demod.symbol_rate:.0f} sym/s "
                f"({vote.note}); CNN model pending"
            )
        else:
            note = kind_note or (
                f"demod {demod.modulation} @ {demod.symbol_rate:.0f} sym/s; "
                "ML vote pending"
            )
        if fec_clean:
            note += f" | FEC {fec.scheme} clean via {fec.deint}"
    else:
        bits_hex, bits_ascii = est.hex_text, est.ascii_text
        corr = {
            "lag": int(est.corr_lag),
            "value": float(est.corr_value),
            "lags": [int(v) for v in est.corr_lags],
            "vals": [float(v) for v in est.corr_vals],
        }
        note = kind_note or (
            "measured from capture preview; classifier pending (later phase)"
            if ingest.kind == "iq"
            else f"wav fs {ingest.fs} Hz from header; I=left/Q=right; classifier pending"
        )
    return {
        "meta": {
            "modulation": modulation,
            "fs": ingest.fs,
            "symbol_rate": symbol_rate,
            "snr_db": round(est.snr_db, 1),
            "center_freq": ingest.fc,
            "file": base,
        },
        "predictions": {
            "modulation": modulation,
            "confidence": confidence,
            "votes": votes,
            "fs_est": ingest.fs,
            "symbol_rate_est": symbol_rate,
            "bw_est": round(float(est.bw_hz), 1),
            "snr_est": round(float(est.snr_db), 1),
        },
        "psd": {
            "freqs": [float(v) for v in est.freqs],
            "mags_db": [float(v) for v in est.mags_db],
        },
        "spectrogram": {
            "times": [float(v) for v in est.spec_times],
            "freqs": [float(v) for v in est.spec_freqs],
            "z_db": [[float(c) for c in row] for row in est.spec_z_db],
        },
        "constellation": {
            "i": [float(v) for v in est.const_i],
            "q": [float(v) for v in est.const_q],
        },
        "bits_preview": {
            "hex": bits_hex,
            "ascii": bits_ascii,
            "corr_peak": corr,
        },
        "comparator": {
            "iq_snr": round(float(est.snr_db), 1),
            "wav_snr": round(float(wav_snr), 1),
            "note": note,
        },
        "log": estimator_log_lines(est),
    }
