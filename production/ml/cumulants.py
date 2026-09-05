"""Cumulant classifier — Phase 5 (classical ML vote, pure NumPy).

Higher-order cumulants separate PSK/QAM/FSK by theory, independent of
the demod slicers (different statistic, rotation-invariant magnitudes):

    unit-power theory (|C20|, |C40|, |C42|):
      BPSK   (1.00, 2.00, 2.00)
      QPSK   (0.00, 1.00, 1.00)
      16QAM  (0.00, 0.68, 0.68)
      2FSK   (0.00, 0.00, 1.00)

Only |.| magnitudes are used (carrier-phase invariant). C42 needs no
carrier coherence at all; C20/C40 need residual drift << 1 cycle over
the window, which the centroid + M=4 derotation below guarantees.
No credible theory match (all distances large) -> UNKNOWN, never a guess.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

CLASSES = ("BPSK", "QPSK", "16QAM", "2FSK")

THEORY: dict[str, tuple[float, float, float]] = {
    "BPSK": (1.00, 2.00, 2.00),
    "QPSK": (0.00, 1.00, 1.00),
    "16QAM": (0.00, 0.68, 0.68),
    "2FSK": (0.00, 0.00, 1.00),
}

UNKNOWN_DIST = 0.75  # best theory distance above this -> UNKNOWN
MIN_SYMBOLS = 64


class CumulantError(ValueError):
    pass


@dataclass
class CumulantResult:
    modulation: str = "UNKNOWN"
    confidence: float = 0.0
    features: np.ndarray = field(repr=False, default_factory=lambda: np.zeros(3))
    ranking: list = field(default_factory=list)  # [(mod, dist)] best-first
    n_symbols: int = 0
    symbols: np.ndarray = field(repr=False, default_factory=lambda: np.zeros(0, dtype=np.complex64))
    dc_ratio: float = 0.0  # |mean|²/power: ~0 spread constellations, ~1 single cluster
    fm_cv: float = 0.0     # std|fm|/mean|fm|: FSK ~0.4, PSK spikes ~2+
    fm_mean: float = 0.0   # mean|fm| in Hz: FSK ~dev, carrier/noise floor low
    note: str = ""


def cumulant_features(sym: np.ndarray) -> np.ndarray:
    """(|C20|, |C40|, |C42|) of unit-power-normalized complex symbols."""
    y = np.asarray(sym, dtype=np.complex128).ravel()
    if y.size < 8:
        raise CumulantError(f"only {y.size} symbols — need >= 8")
    pwr = float(np.mean(np.abs(y) ** 2))
    if pwr <= 0:
        raise CumulantError("zero-power symbols")
    y = y / np.sqrt(pwr)
    m20 = np.mean(y**2)
    m21 = np.mean(np.abs(y) ** 2)  # == 1 after normalize; kept for clarity
    m40 = np.mean(y**4)
    m42 = np.mean(np.abs(y) ** 4)
    c20 = m20
    c40 = m40 - 3.0 * m20**2
    c42 = m42 - abs(m20) ** 2 - 2.0 * m21**2
    return np.array([abs(c20), abs(c40), abs(c42)], dtype=float)


def classify_features(feat: np.ndarray) -> CumulantResult:
    """Nearest-theory vote on a feature triple. UNKNOWN when nothing matches."""
    feat = np.asarray(feat, dtype=float).ravel()
    if feat.size != 3:
        raise CumulantError(f"need 3 features, got {feat.size}")
    ranking = sorted(
        ((mod, float(np.linalg.norm(feat - np.array(THEORY[mod])))) for mod in CLASSES),
        key=lambda kv: kv[1],
    )
    (best, d1), (_, d2) = ranking[0], ranking[1]
    if d1 > UNKNOWN_DIST:
        return CumulantResult(
            features=feat, ranking=ranking,
            note=f"no theory match (best {best} dist {d1:.2f} > {UNKNOWN_DIST})",
        )
    conf = (d2 - d1) / (d2 + d1 + 1e-9)
    return CumulantResult(
        modulation=best,
        confidence=float(min(0.95, max(0.05, conf))),
        features=feat, ranking=ranking,
        note=f"cumulants {best} (dist {d1:.2f}, runner-up {d2:.2f})",
    )


def classify_preview(preview: np.ndarray, fs: int) -> CumulantResult:
    """Full cumulant chain on one ingest preview (own correction, no demod state)."""
    from engine.demod import (
        derotate,
        estimate_carrier,
        estimate_symbol_rate,
        fm_stream,
        mix_down,
        refine_freq,
        timing_search,
        _to_2sps,
    )

    if not fs or fs <= 0:
        raise CumulantError(f"bad sample rate fs={fs}")
    x = np.asarray(preview, dtype=np.complex64).ravel()
    if x.size == 0:
        raise CumulantError("empty preview")
    coarse = estimate_carrier(x, fs)
    x_bb = mix_down(x, fs, coarse)
    fm = fm_stream(x_bb, fs)
    fm_abs = np.abs(fm)
    fm_mean = float(np.mean(fm_abs))
    fm_cv = float(np.std(fm_abs) / (fm_mean + 1e-12))
    rate, _method = estimate_symbol_rate(x_bb, fs)
    if rate <= 0:
        return CumulantResult(fm_cv=fm_cv, note="no symbol-rate line — cumulants abstain")
    sps = float(fs) / float(rate)
    if sps < 2.0 or len(x) / sps < MIN_SYMBOLS:
        return CumulantResult(fm_cv=fm_cv, note=f"sps {sps:.1f} — too few symbols, cumulants abstain")
    try:
        sym, _tau = timing_search(_to_2sps(x_bb, sps))
    except Exception as exc:
        return CumulantResult(fm_cv=fm_cv, note=f"timing failed ({exc}) — cumulants abstain")
    sym = np.asarray(sym[:4096])  # cap: moments converge long before 4k symbols
    dc_ratio = float(abs(np.mean(sym)) ** 2 / (np.mean(np.abs(sym) ** 2) + 1e-30))
    try:
        feat_raw = cumulant_features(sym)
    except CumulantError:
        feat_raw = None
    if feat_raw is not None:
        raw = classify_features(feat_raw)
        raw.n_symbols = len(sym)
        raw.symbols = sym.astype(np.complex64)
        raw.dc_ratio = dc_ratio
        raw.fm_cv = fm_cv
        raw.fm_mean = fm_mean
        # FSK-first: M=4 derotation below phase-locks FSK's 4th power into
        # false coherence, so FSK must be caught on RAW timed symbols. The
        # FM gate is essential: drifted PSK also lands near (0,0,1) raw,
        # but only FSK has tight loud FM (cv < 0.85, mean > 1kHz).
        if raw.modulation == "2FSK" and fm_cv < 0.85 and fm_mean > 1000.0:
            raw.confidence = float(min(0.95, max(raw.confidence, 1.1 - fm_cv)))
            raw.note += f"; tight loud FM (cv {fm_cv:.2f}) confirms 2FSK"
            return raw
    if dc_ratio > 0.25:
        # Single off-center cluster: degenerate FSK (dev locked to a multiple
        # of baud, so 1-sps phases freeze) or an unmodulated carrier. All
        # three must hold for the FSK call: clustered + tight FM + loud FM
        # (a carrier's FM is noise-floor quiet; PSK never clusters here).
        if fm_cv < 0.6 and fm_mean > 1000.0:
            res = CumulantResult(
                modulation="2FSK", confidence=float(min(0.9, max(0.4, 1.2 - fm_cv))),
                n_symbols=len(sym), symbols=sym.astype(np.complex64),
                dc_ratio=dc_ratio, fm_cv=fm_cv, fm_mean=fm_mean,
                note=f"single-cluster + tight loud FM (dc {dc_ratio:.2f}, "
                     f"fm {fm_mean:.0f}Hz cv {fm_cv:.2f}) → 2FSK",
            )
            try:
                res.features = cumulant_features(sym)
                res.ranking = sorted(
                    ((m, float(np.linalg.norm(res.features - np.array(THEORY[m])))) for m in CLASSES),
                    key=lambda kv: kv[1],
                )
            except CumulantError:
                pass
            return res
        return CumulantResult(
            dc_ratio=dc_ratio, fm_cv=fm_cv, fm_mean=fm_mean,
            note=f"single cluster without FSK FM signature (dc {dc_ratio:.2f}) — abstain",
        )
    sym = derotate(sym, sps, fs, refine_freq(sym, sps, fs, 4))
    try:
        feat = cumulant_features(sym)
    except CumulantError as exc:
        return CumulantResult(fm_cv=fm_cv, note=f"{exc} — cumulants abstain")
    res = classify_features(feat)
    res.n_symbols = len(sym)
    res.symbols = sym.astype(np.complex64)
    res.dc_ratio = dc_ratio
    res.fm_cv = fm_cv
    res.fm_mean = fm_mean
    return res


def cumulant_log_lines(c: CumulantResult) -> list[str]:
    if c.modulation == "UNKNOWN":
        return [f"cumulants: abstain — {c.note}"]
    f = c.features
    rank = ", ".join(f"{m} {d:.2f}" for m, d in c.ranking)
    return [
        f"cumulants: {c.modulation} ({c.confidence:.2f}; "
        f"|C20| {f[0]:.2f} |C40| {f[1]:.2f} |C42| {f[2]:.2f} from {c.n_symbols} sym)",
        f"cumulant rank [{rank}]",
    ]
