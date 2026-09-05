"""Demod — Phase 4.

Real demodulation on an IngestResult.preview (complex64):
carrier correction -> symbol-rate estimate -> timing search ->
try-all {BPSK, QPSK, 16QAM, 2FSK} ranked by EVM -> bits -> hex/ascii ->
sync-word finder (numpy.correlate) + header/payload split.

Pure NumPy (+ SciPy-free on purpose: all ops are FFT/interp/correlate).
Costas/PLL is simplified per the locked stack: coarse power-centroid
mix-down + one M=4 (QPSK-grade) fine-frequency pass. Numba/Viterbi and
Gardner-loop refinements land in later hardening passes; API stays stable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

CANDIDATES = ("BPSK", "QPSK", "16QAM", "2FSK")

# Sync-word library (bits, 0/1). Correlated in bipolar form.
PREAMBLES: dict[str, list[int]] = {
    "BARKER13": [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    "BARKER11": [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    "ALT16": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    "PRE16": [1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
}

SYNC_SEARCH_BITS = 4096  # only the head of the stream is searched
CORR_N = 256             # widget contract: 256 corr points
MAX_SYMBOLS = 20000      # cap 1-sps symbols materialized
TIMING_GRID = 32         # fractional-offset candidates in [0, 1)
UNKNOWN_EVM_DB = -4.0    # best EVM worse than this -> modulation UNKNOWN


class DemodError(ValueError):
    pass


@dataclass
class DemodResult:
    modulation: str = "UNKNOWN"   # BPSK | QPSK | 16QAM | 2FSK | UNKNOWN
    symbol_rate: float = 0.0
    n_symbols: int = 0
    bits: np.ndarray = field(repr=False, default_factory=lambda: np.zeros(0, dtype=np.uint8))
    evm_db: float = 0.0           # best candidate EVM
    margin_db: float = 0.0        # runner-up EVM minus best (decision confidence proxy)
    freq_offset: float = 0.0      # total carrier correction applied (Hz)
    hex_text: str = "(no bits)"
    ascii_text: str = "(no bits)"
    sync_word: str = "none"
    sync_lag: int = 0
    sync_value: float = 0.0
    header_bits: int = 0
    payload_bits: int = 0
    corr_lags: np.ndarray = field(repr=False, default_factory=lambda: np.arange(CORR_N))
    corr_vals: np.ndarray = field(repr=False, default_factory=lambda: np.zeros(CORR_N))
    candidates: list = field(default_factory=list)  # [(mod, evm_db)] sorted best-first
    note: str = ""


def _as_complex(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.complex64).ravel()
    if arr.size == 0:
        raise DemodError("empty preview — nothing to demodulate")
    return arr


def estimate_carrier(x: np.ndarray, fs: int, n_fft: int = 32768) -> float:
    """Power-centroid carrier offset (Hz). ~0 for symmetric baseband, mid-tone for FSK."""
    x = _as_complex(x)
    seg = np.asarray(x[:n_fft], dtype=np.complex128)
    seg = seg * np.hanning(len(seg))
    spec = np.abs(np.fft.fftshift(np.fft.fft(seg))) ** 2
    freqs = np.linspace(-fs / 2.0, fs / 2.0, len(seg))
    floor = float(np.median(spec))
    w = np.clip(spec - floor, 0.0, None)
    if w.sum() <= 0:
        return 0.0
    return float(np.sum(freqs * w) / np.sum(w))


def mix_down(x: np.ndarray, fs: int, offset_hz: float) -> np.ndarray:
    """Rotate by -offset_hz (complex baseband correction)."""
    x = _as_complex(x)
    if offset_hz == 0.0:
        return x
    t = np.arange(len(x), dtype=np.float64) / float(fs)
    return (x.astype(np.complex128) * np.exp(-2j * np.pi * float(offset_hz) * t)).astype(np.complex64)


def fm_stream(x: np.ndarray, fs: int) -> np.ndarray:
    """Instantaneous frequency (Hz) via phase-difference discriminator."""
    x = _as_complex(x)
    d = np.angle(np.conj(x[:-1].astype(np.complex128)) * x[1:].astype(np.complex128))
    return (d * float(fs) / (2.0 * np.pi)).astype(float)


RATE_SEARCH_MAX = 65536  # samples entering baud estimation (FFT autocorr is O(N log N))


def _fft_autocorr(e: np.ndarray) -> np.ndarray:
    """Normalized autocorrelation via FFT (fast even for 262k previews)."""
    e = np.asarray(e, dtype=float).ravel()
    e = e - e.mean()
    if np.all(e == 0):
        return np.zeros(1)
    n = 1
    while n < 2 * len(e):
        n *= 2
    f = np.fft.rfft(e, n=n)
    ac = np.fft.irfft(np.abs(f) ** 2, n=n)[: len(e)]
    return ac / max(ac[0], 1e-30)


def _nrz_coarse_sps(sig: np.ndarray, fs: int) -> float:
    """Coarse samples/symbol from NRZ triangle decay (I/Q/fm are all NRZ-ish).

    Random-pulse streams decorrelate linearly (1-|k|/sps), crossing 0.5 at
    sps/2 — scale-free, no amplitude threshold. White noise decorrelates
    instantly (ac[1] ~= 0) and is rejected by the gate.
    """
    e = np.asarray(sig, dtype=float).ravel()[:RATE_SEARCH_MAX]
    if len(e) < 16:
        return 0.0
    ac = _fft_autocorr(e)
    if len(ac) < 8 or ac[1] < 0.5:
        return 0.0
    hi = min(len(ac) - 1, int(fs // 50))  # baud >= 50 Hz
    for i in range(2, hi):
        if ac[i - 1] >= 0.5 > ac[i]:
            frac = (ac[i - 1] - 0.5) / max(ac[i - 1] - ac[i], 1e-12)
            return 2.0 * (i - 1.0 + float(np.clip(frac, 0.0, 1.0)))
    return 0.0


def _refine_sps(edge_ac: np.ndarray, coarse: float) -> tuple[float, float]:
    """Exact (fractional) sps by maximizing edge periodicity near coarse.

    The edge spike train peaks exactly at multiples of sps; argmax over a
    +-15% window plus parabolic interpolation beats any global threshold.
    Returns (sps, peak_value); peak ~0 means aperiodic (noise).
    """
    n = len(edge_ac)
    lo = max(2, int(coarse * 0.85))
    hi = min(n - 2, int(round(coarse * 1.15)) + 1)
    if hi <= lo:
        return 0.0, 0.0
    seg = edge_ac[lo:hi]
    j = int(np.argmax(seg))
    peak = float(seg[j])
    lag = lo + j
    if 0 < j < len(seg) - 1:
        a, b, c = float(seg[j - 1]), peak, float(seg[j + 1])
        denom = a - 2 * b + c
        shift = 0.5 * (a - c) / denom if denom != 0 else 0.0
        lag = lag + float(np.clip(shift, -1.0, 1.0))
    return lag, peak


def _baud_from_pair(nrz: np.ndarray, edge: np.ndarray, fs: int) -> tuple[float, float]:
    coarse = _nrz_coarse_sps(nrz, fs)
    if coarse < 2.0:
        return 0.0, 0.0
    e = np.asarray(edge, dtype=float).ravel()[:RATE_SEARCH_MAX]
    if len(e) < 16:
        return 0.0, 0.0
    sps, peak = _refine_sps(_fft_autocorr(e), coarse)
    if sps < 2.0 or peak < 0.05:
        return 0.0, 0.0
    return float(fs) / sps, peak


def estimate_symbol_rate(x_bb: np.ndarray, fs: int) -> tuple[float, str]:
    """Baud estimate: NRZ-triangle coarse sps refined by edge periodicity.

    I, Q and FM-deviation streams are all NRZ-ish for rectangular and
    band-limited pulses alike (constant-envelope BPSK/QPSK and FSK
    included — the FM stream carries FSK's baud). Each voter pairs its
    NRZ stream (coarse, scale-free) with its boundary-edge stream
    (exact fractional sps); the strongest edge periodicity wins.

    Returns (rate_hz, method). Rate 0.0 = no credible line found.
    """
    x_bb = _as_complex(x_bb)
    xc = x_bb.astype(np.complex128)
    edge_c = np.abs(np.diff(xc)) ** 2
    fm = fm_stream(x_bb, fs)
    signed = np.sign(fm - np.median(fm)).astype(float)
    voters = [
        (xc.real, edge_c, "edge-I"),
        (xc.imag, edge_c, "edge-Q"),
        (fm, np.abs(np.diff(fm)), "fm-edge"),
        (signed, np.abs(np.diff(signed)), "fm-sign"),
    ]
    ranked = sorted(
        ((rate, peak, name) for (rate, peak), name in
         [(_baud_from_pair(nrz, edge, fs), name) for nrz, edge, name in voters]),
        key=lambda t: t[1],
    )
    (rate, peak, method) = ranked[-1]
    if peak <= 0.0:
        return 0.0, "none"
    return rate, method


def _to_2sps(values: np.ndarray, sps: float) -> np.ndarray:
    """Resample a sample stream (complex or real) to exactly 2 samples/symbol."""
    v = np.asarray(values)
    n_sym = int(len(v) // sps)
    if n_sym < 4:
        raise DemodError(f"only {n_sym} symbols at {sps:.1f} sps — need >= 4")
    n_sym = min(n_sym, MAX_SYMBOLS)
    idx = np.arange(n_sym * 2, dtype=np.float64) * (sps / 2.0)
    grid = np.arange(len(v), dtype=np.float64)
    if np.iscomplexobj(v):
        return np.interp(idx, grid, v.real) + 1j * np.interp(idx, grid, v.imag)
    return np.interp(idx, grid, v.astype(float))


def timing_search(y2: np.ndarray) -> tuple[np.ndarray, float]:
    """Max-energy fractional timing search over TIMING_GRID offsets in [0, 1).

    y2: 2-sps stream (complex PSK/QAM or real FM). Symbol centers carry
    full amplitude (rectangular) or peak energy (band-limited), while
    transition samples sit near zero — so argmax of the 1-sps energy
    finds symbol centers for both pulse shapes. (A min-difference metric
    was tried: it locks onto transitions for rectangular pulses because
    mid-symbol full-swing jumps look "larger" than smeared edges.)
    Residual carrier spin is NOT handled here — _phase_track derotates
    after slicing. Returns (1-sps symbols, tau).
    """
    y2 = np.asarray(y2)
    n_sym = len(y2) // 2
    cap = min(n_sym, 8000)
    seg = y2[: cap * 2]
    grid = np.arange(len(seg), dtype=np.float64)
    taus = np.linspace(0.0, 1.0, TIMING_GRID, endpoint=False)
    best_tau, best_metric = 0.0, -np.inf
    for tau in taus:
        idx = (np.arange(cap, dtype=np.float64) + tau) * 2.0
        if np.iscomplexobj(seg):
            y = np.interp(idx, grid, seg.real) + 1j * np.interp(idx, grid, seg.imag)
            metric = float(np.mean(np.abs(y) ** 2))
        else:
            y = np.interp(idx, grid, seg.astype(float))
            metric = float(np.var(y))
        if metric > best_metric:
            best_metric, best_tau = metric, float(tau)
    full_n = len(y2) // 2
    fgrid = np.arange(len(y2), dtype=np.float64)
    fidx = (np.arange(full_n, dtype=np.float64) + best_tau) * 2.0
    if np.iscomplexobj(y2):
        sym = np.interp(fidx, fgrid, y2.real) + 1j * np.interp(fidx, fgrid, y2.imag)
    else:
        sym = np.interp(fidx, fgrid, y2.astype(float))
    return sym, best_tau


def refine_freq(sym: np.ndarray, sps: float, fs: int, order: int) -> float:
    """Residual carrier from M-th-power tone on 1-sps symbols (Hz).

    The M-th power strips modulation (order 2 BPSK, 4 QPSK/16QAM),
    leaving a tone at order*f_res. Zero-padded FFT + parabolic
    interpolation gives sub-Hz accuracy; range limited to ±rate/8
    (coarse mix-down guarantees the residual is small).
    """
    y = np.asarray(sym, dtype=np.complex128).ravel()
    if len(y) < 16:
        return 0.0
    rate = float(fs) / float(sps)
    z = y**order
    n = 1
    while n < 4 * len(z):
        n *= 2
    spec = np.abs(np.fft.fft(z, n=n)) ** 2
    freqs = np.fft.fftfreq(n, 1.0 / rate)  # symbol-rate domain
    peak = int(np.argmax(spec))
    if 0 < peak < n - 1 and spec[peak] > 0:
        a, b, c = spec[peak - 1], spec[peak], spec[peak + 1]
        denom = a - 2 * b + c
        shift = 0.5 * (a - c) / denom if denom != 0 else 0.0
        shift = float(np.clip(shift, -1.0, 1.0))
    else:
        shift = 0.0
    f_m = (freqs[peak] + shift * (rate / n)) / order
    return float(f_m) if abs(f_m) <= rate / 8.0 else 0.0


def derotate(sym: np.ndarray, sps: float, fs: int, f_hz: float) -> np.ndarray:
    y = np.asarray(sym, dtype=np.complex128)
    if f_hz == 0.0:
        return y
    t = np.arange(len(y), dtype=np.float64) * float(sps) / float(fs)
    return y * np.exp(-2j * np.pi * float(f_hz) * t)
def _best_of(sym_raw: np.ndarray, sym_tracked: np.ndarray, slicer) -> tuple[np.ndarray, np.ndarray, float]:
    """Slice both raw and phase-tracked symbols; keep the lower EVM.

    Tracking rescues fast residual drift but can dither an already-clean
    frame (e.g. M=4 branch-cut flips on diagonal constellations), so the
    raw frame always competes as a candidate.
    """
    best = None
    for sym in (sym_raw, sym_tracked):
        bits, ideal, evm = slicer(sym)
        if best is None or evm < best[2]:
            best = (bits, ideal, evm)
    assert best is not None
    return best
def _phase_track(sym: np.ndarray, order: int, n_iter: int = 2, block: int = 256) -> np.ndarray:
    """Decision-directed carrier-phase tracking (simplified Costas/PLL).

    Residual drift after mix-down would spin the constellation over long
    previews. Per-block M-th-power phase averaging (order 2 BPSK, 4
    QPSK/16QAM) estimates the drift without decision ambiguity, then the
    symbols are de-rotated. Two passes suffice for the residuals left by
    estimate_carrier.
    """
    y = np.asarray(sym, dtype=np.complex128)
    n = len(y)
    if n < 8:
        return y
    idx = np.arange(n)
    for _ in range(n_iter):
        zm = y**order
        nb = max(1, int(np.ceil(n / block)))
        grid = (np.arange(nb) + 0.5) * block
        means = np.array([
            np.angle(np.mean(zm[i * block:(i + 1) * block])) / order
            for i in range(nb)
        ])
        phi = np.interp(idx, grid, np.unwrap(means * order) / order,
                        left=means[0], right=means[-1])
        y = y * np.exp(-1j * phi)
    return y


def _evm_db(err_pwr: float, ref_pwr: float) -> float:
    return float(10.0 * np.log10(max(err_pwr, 1e-30) / max(ref_pwr, 1e-30)))


def _slice_bpsk(sym: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Try phases {0, pi}; returns (bits, ideal_symbols, evm_db) for best phase."""
    best = None
    for phi in (0.0, np.pi):
        rot = sym * np.exp(1j * phi)
        bits = (rot.real >= 0).astype(np.uint8)
        ideal = np.where(bits, 1.0, -1.0)
        evm = _evm_db(np.mean(np.abs(rot - ideal) ** 2), 1.0)
        if best is None or evm < best[2]:
            best = (bits, ideal.astype(complex), evm)
    assert best is not None
    return best


def _slice_qpsk(sym: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Try 4 quadrant phases; 2 bits/symbol (b0 = I>=0, b1 = Q>=0)."""
    const = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2.0)
    best = None
    for k in range(4):
        rot = sym * np.exp(1j * k * np.pi / 2.0)
        dists = np.abs(rot[:, None] - const[None, :])
        pick = np.argmin(dists, axis=1)
        ideal = const[pick]
        bits = np.empty(2 * len(sym), dtype=np.uint8)
        bits[0::2] = (rot.real >= 0).astype(np.uint8)
        bits[1::2] = (rot.imag >= 0).astype(np.uint8)
        evm = _evm_db(np.mean(dists[np.arange(len(sym)), pick] ** 2), 1.0)
        if best is None or evm < best[2]:
            best = (bits, ideal, evm)
    assert best is not None
    return best


_QAM_LEVELS = np.array([-3.0, -1.0, 1.0, 3.0]) / np.sqrt(10.0)


def _slice_qam16(sym: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Unit-power normalize, 4 quadrant phases, nearest of 16 ideals, 4 bits/symbol."""
    pwr = float(np.mean(np.abs(sym) ** 2))
    if pwr <= 0:
        return np.zeros(0, dtype=np.uint8), np.zeros(0, dtype=complex), 0.0
    norm = sym / np.sqrt(pwr)
    grid = _QAM_LEVELS
    ideals = np.array([r + 1j * c for r in grid for c in grid])
    best = None
    for k in range(4):
        rot = norm * np.exp(1j * k * np.pi / 2.0)
        dists = np.abs(rot[:, None] - ideals[None, :])
        pick = np.argmin(dists, axis=1)
        ideal = ideals[pick]
        ri = np.argmin(np.abs(rot.real[:, None] - grid[None, :]), axis=1)
        qi = np.argmin(np.abs(rot.imag[:, None] - grid[None, :]), axis=1)
        bits = np.empty(4 * len(sym), dtype=np.uint8)
        bits[0::4] = (ri // 2).astype(np.uint8)
        bits[1::4] = (ri % 2).astype(np.uint8)
        bits[2::4] = (qi // 2).astype(np.uint8)
        bits[3::4] = (qi % 2).astype(np.uint8)
        evm = _evm_db(np.mean(dists[np.arange(len(sym)), pick] ** 2), 1.0)
        if best is None or evm < best[2]:
            best = (bits, ideal, evm)
    assert best is not None
    return best


def _dump_at(fm: np.ndarray, c: np.ndarray, sps: float, shift: float) -> np.ndarray:
    """Mean FM over middle half-symbols with grid shifted by `shift` samples."""
    n = len(fm)
    n_sym = min(int(n // sps), MAX_SYMBOLS)
    if n_sym < 1:
        return np.zeros(0)
    centers = np.arange(n_sym, dtype=np.float64) * sps + shift
    half = sps / 4.0
    lo = np.clip(np.round(centers - half).astype(int), 0, n - 1)
    hi = np.clip(np.round(centers + half).astype(int), lo + 1, n)
    return (c[hi] - c[lo]) / np.maximum(hi - lo, 1)


def _fsk_dump(fm: np.ndarray, sps: float, tau: float) -> np.ndarray:
    """Integrate-and-dump: mean FM over the middle half of each symbol.

    Per-sample discriminator noise (~fs-dependent) dominates single-sample
    decisions; averaging the middle half-symbol (matched filter for
    rectangular FSK, transients excluded) cuts noise by ~sqrt(sps/2) and
    makes FSK EVM comparable with coherent PSK scores. The timing grid
    from timing_search is ambiguous by half a symbol for rectangular
    pulses (boundary-first-samples read clean), so both grid phases are
    dumped and the higher-variance one — the true mid-symbol phase —
    is kept. Vectorized via cumsum. Returns 1-sps real symbols.
    """
    fm = np.asarray(fm, dtype=float).ravel()
    if len(fm) < sps:
        return np.zeros(0)
    c = np.concatenate([[0.0], np.cumsum(fm)])
    grid_shift = tau * sps
    a = _dump_at(fm, c, sps, grid_shift)
    b = _dump_at(fm, c, sps, grid_shift + sps / 2.0)
    if len(a) == 0:
        return b
    if len(b) == 0:
        return a
    n = min(len(a), len(b))
    return a[:n] if float(np.var(a[:n])) >= float(np.var(b[:n])) else b[:n]
def _demod_fsk_symbols(fm_sym: np.ndarray) -> tuple[np.ndarray, float]:
    """Slice real FM symbols; EVM vs +/-dev_est decision levels."""
    fm = np.asarray(fm_sym, dtype=float)
    dev = float(np.mean(np.abs(fm)))
    if dev <= 0:
        return np.zeros(0, dtype=np.uint8), 0.0
    bits = (fm >= 0).astype(np.uint8)
    decided = np.where(bits, dev, -dev)
    return bits, _evm_db(np.mean((fm - decided) ** 2), dev**2)


def bits_to_hex_ascii(bits: np.ndarray, n_bytes: int = 32) -> tuple[str, str]:
    bits = np.asarray(bits, dtype=np.uint8).ravel()
    nbytes = min(n_bytes, len(bits) // 8)
    if nbytes == 0:
        return "(no bits)", "(no bits)"
    raw = np.packbits(bits[: nbytes * 8]).tobytes()
    hex_text = " ".join(f"{b:02X}" for b in raw)
    ascii_text = "".join(chr(b) if 32 <= b < 127 else "." for b in raw)
    return hex_text, ascii_text


def sync_search(bits: np.ndarray) -> tuple[str, int, float, np.ndarray, np.ndarray]:
    """Correlate bipolar bit head against the preamble library.

    Returns (name, lag_bits, value, lags(256,), vals(256,)) where lags/vals
    window the best preamble's correlation around its peak for the widget.
    """
    bits = np.asarray(bits, dtype=np.uint8).ravel()
    head = bits[:SYNC_SEARCH_BITS]
    if len(head) < 16:
        return "none", 0, 0.0, np.arange(CORR_N), np.zeros(CORR_N)
    stream = head.astype(float) * 2.0 - 1.0
    best_name, best_lag, best_val = "none", 0, 0.0
    best_corr: np.ndarray | None = None
    for name, pre in PREAMBLES.items():
        ref = np.array(pre, dtype=float) * 2.0 - 1.0
        if len(ref) >= len(stream):
            continue
        corr = np.correlate(stream, ref, mode="valid") / len(ref)
        lag = int(np.argmax(np.abs(corr)))
        val = float(corr[lag])
        if best_corr is None or abs(val) > abs(best_val):
            best_name, best_lag, best_val, best_corr = name, lag, val, corr
    if best_corr is None:
        return "none", 0, 0.0, np.arange(CORR_N), np.zeros(CORR_N)
    n = len(best_corr)
    lo = max(0, min(best_lag - CORR_N // 2, n - CORR_N))
    seg = best_corr[lo: lo + CORR_N]
    if len(seg) < CORR_N:  # short stream: pad
        seg = np.pad(seg, (0, CORR_N - len(seg)))
    lags = np.arange(lo, lo + CORR_N)
    peak_in_window = best_lag - lo if 0 <= best_lag - lo < CORR_N else int(np.argmax(np.abs(seg)))
    return best_name, int(lags[peak_in_window]), float(seg[peak_in_window]), lags.astype(int), seg.astype(float)


def demodulate_preview(preview: np.ndarray, fs: int) -> DemodResult:
    """Full Phase-4 chain on one ingest preview. Never raises on weak signals —
    returns modulation UNKNOWN with a note (raises only on empty/bad input)."""
    if not fs or fs <= 0:
        raise DemodError(f"bad sample rate fs={fs}")
    x = _as_complex(preview)

    # 1. Carrier correction: coarse centroid + M=4 fine pass (PSK-grade).
    coarse = estimate_carrier(x, fs)
    x_bb = mix_down(x, fs, coarse)
    fine = estimate_carrier(x_bb**4, fs) / 4.0 if len(x_bb) >= 64 else 0.0
    if abs(fine) > fs / 4.0:  # M=4 alias guard (FSK/wideband can alias)
        fine = 0.0
    x_bb = mix_down(x_bb, fs, fine)
    freq_offset = float(coarse + fine)

    # 2. Symbol rate.
    rate, method = estimate_symbol_rate(x_bb, fs)
    if rate <= 0:
        return DemodResult(
            freq_offset=freq_offset,
            note=f"no symbol-rate line found ({method}); showing estimator-only view",
        )
    sps = float(fs) / float(rate)
    if sps < 2.0 or len(x) / sps < 16:
        return DemodResult(
            freq_offset=freq_offset, symbol_rate=float(rate),
            note=f"sps {sps:.1f} < 2 or <16 symbols — undersampled for demod",
        )

    # 3. Timing + try-all candidates.
    try:
        y2_c = _to_2sps(x_bb, sps)
        sym_c, _tau = timing_search(y2_c)
        fm = fm_stream(x_bb, fs)
        y2_f = _to_2sps(fm, sps)
        _, tau_f = timing_search(y2_f)
        fm_sym = _fsk_dump(fm, sps, tau_f)  # integrate-and-dump beats raw samples
    except DemodError as exc:
        return DemodResult(freq_offset=freq_offset, symbol_rate=float(rate), note=str(exc))

    scored: dict[str, tuple[np.ndarray, float]] = {}
    sym_b_raw = derotate(sym_c, sps, fs, refine_freq(sym_c, sps, fs, 2))
    bits_b, _, evm_b = _best_of(sym_b_raw, _phase_track(sym_b_raw, order=2), _slice_bpsk)
    scored["BPSK"] = (bits_b, evm_b)
    sym_q_raw = derotate(sym_c, sps, fs, refine_freq(sym_c, sps, fs, 4))
    bits_q, _, evm_q = _best_of(sym_q_raw, _phase_track(sym_q_raw, order=4), _slice_qpsk)
    scored["QPSK"] = (bits_q, evm_q)
    bits_m, _, evm_m = _best_of(sym_q_raw, _phase_track(sym_q_raw, order=4), _slice_qam16)
    scored["16QAM"] = (bits_m, evm_m)  # QAM16 shares QPSK-grade correction
    bits_f, evm_f = _demod_fsk_symbols(fm_sym)
    scored["2FSK"] = (bits_f, evm_f)

    # Rank by complexity-penalized EVM: richer constellations always fit
    # noise better, so each candidate pays 10*log10(bits/symbol) dB
    # (BPSK/2FSK +0, QPSK +3, 16QAM +6) before comparison.
    _BPS = {"BPSK": 1, "QPSK": 2, "16QAM": 4, "2FSK": 1}
    penalized = {m: e + 10.0 * np.log10(_BPS[m]) for m, (_, e) in scored.items()}
    ranked = sorted(scored.items(), key=lambda kv: penalized[kv[0]])
    (winner, (wbits, wevm)), runner = ranked[0], ranked[1]
    margin = float(penalized[runner[0]] - penalized[winner])
    if penalized[winner] > UNKNOWN_EVM_DB:
        return DemodResult(
            freq_offset=freq_offset, symbol_rate=float(rate),
            evm_db=float(wevm), margin_db=float(margin),
            candidates=[(m, float(e)) for m, (_, e) in ranked],
            note=f"all candidates EVM > {UNKNOWN_EVM_DB:.0f} dB — no credible demod",
        )

    # 4. Bits products + sync search + header/payload split.
    hex_text, ascii_text = bits_to_hex_ascii(wbits)
    sname, slag, sval, slags, svals = sync_search(wbits)
    pre_len = len(PREAMBLES.get(sname, []))
    header_bits = slag + pre_len if sname != "none" and abs(sval) >= 0.5 else 0
    payload_bits = max(0, len(wbits) - header_bits)
    return DemodResult(
        modulation=winner, symbol_rate=float(rate), n_symbols=int(len(sym_c)),
        bits=wbits, evm_db=float(wevm), margin_db=float(margin),
        freq_offset=freq_offset, hex_text=hex_text, ascii_text=ascii_text,
        sync_word=sname, sync_lag=int(slag), sync_value=float(sval),
        header_bits=int(header_bits), payload_bits=int(payload_bits),
        corr_lags=slags, corr_vals=svals,
        candidates=[(m, float(e)) for m, (_, e) in ranked],
        note=f"rate {rate:.0f} sym/s via {method}; EVM {wevm:.1f} dB, margin {margin:.1f} dB",
    )


def demod_log_lines(d: DemodResult) -> list[str]:
    if d.modulation == "UNKNOWN":
        return [f"demod: UNKNOWN — {d.note}"]
    rank = ", ".join(f"{m} {e:.1f}dB" for m, e in d.candidates)
    lines = [
        f"demod: {d.modulation} @ {d.symbol_rate:.0f} sym/s "
        f"({d.n_symbols} sym, EVM {d.evm_db:.1f} dB, margin {d.margin_db:.1f} dB)",
        f"carrier corrected {d.freq_offset:.1f} Hz; rank [{rank}]",
    ]
    if d.sync_word != "none" and abs(d.sync_value) >= 0.5:
        lines.append(
            f"sync {d.sync_word} @ bit {d.sync_lag} (corr {d.sync_value:.2f}); "
            f"header {d.header_bits}b, payload {d.payload_bits}b"
        )
    else:
        lines.append(f"sync: no preamble lock (best {d.sync_word} {d.sync_value:.2f})")
    return lines
