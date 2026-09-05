"""Vote ensemble — Phase 5.

Weighted poll of independent voters:
  demod      (EVM try-all, weight 0.45)
  cumulants   (theory table, weight 0.25)
  sklearn     (RandomForest on 5 DSP features, weight 0.30)
  cnn        (ONNX model, weight 0.00 until a model file exists)

ABSTAIN > GUESS: UNKNOWN voters contribute no weight; total abstention
stays UNKNOWN. A winner that overrides the demod is flagged and its
confidence tempered.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from ml.cumulants import CLASSES, CumulantResult

WEIGHTS = {"demod": 0.45, "cumulants": 0.25, "sklearn": 0.30, "cnn": 0.00}

_MODEL = None  # lazily trained RandomForest (single GUI thread for now)
_TRAIN_SECS = 0.0


def _sklearn_features(cum: CumulantResult, fm_cv: float) -> np.ndarray:
    """6-DSP-feature row: 3 cumulants + envelope CV + FM CV + DC ratio."""
    f = np.asarray(cum.features, dtype=float).ravel()
    sym = np.asarray(cum.symbols)
    mag = np.abs(sym.astype(np.complex128))
    env_cv = float(np.std(mag) / (np.mean(mag) + 1e-12)) if mag.size else 0.0
    dc = float(getattr(cum, "dc_ratio", 0.0))
    return np.array([f[0], f[1], f[2], env_cv, float(fm_cv), dc], dtype=float)


def _fm_cv(preview: np.ndarray, fs: int) -> float:
    from engine.demod import estimate_carrier, fm_stream, mix_down

    x_bb = mix_down(
        np.asarray(preview, dtype=np.complex64).ravel(), fs,
        estimate_carrier(preview, fs),
    )
    fm = np.abs(fm_stream(x_bb, fs))
    return float(np.std(fm) / (np.mean(fm) + 1e-12))


def get_model():
    """Lazily train the RandomForest on the deterministic synth set (once)."""
    global _MODEL, _TRAIN_SECS
    if _MODEL is not None:
        return _MODEL
    try:
        from sklearn.ensemble import RandomForestClassifier
    except ImportError as exc:
        raise ImportError("scikit-learn is required for the sklearn vote") from exc
    from ml.cumulants import classify_preview
    from ml.synth import FS as SYNTH_FS
    from ml.synth import training_set

    t0 = time.time()
    xs, ys = training_set()
    rows, labels = [], []
    skipped = 0
    for x, mod in zip(xs, ys):
        cum = classify_preview(x, SYNTH_FS)
        if cum.n_symbols == 0:
            skipped += 1  # below sensitivity (short burst + low SNR): abstain, don't train on zeros
            continue
        rows.append(_sklearn_features(cum, _fm_cv(x, SYNTH_FS)))
        labels.append(mod)
    X = np.vstack(rows)
    if not np.all(np.isfinite(X)):
        raise ValueError("non-finite sklearn training features")
    if len(set(labels)) < 2:
        raise ValueError(f"only {len(set(labels))} class(es) above sensitivity — need >= 2")
    _MODEL = RandomForestClassifier(
        n_estimators=64, max_depth=6, min_samples_leaf=2, random_state=7
    )
    _MODEL.fit(X, labels)
    _TRAIN_SECS = time.time() - t0
    return _MODEL


def sklearn_predict(preview: np.ndarray, fs: int, cum: CumulantResult | None = None):
    """(modulation, proba). UNKNOWN on any failure (abstain, never guess)."""
    from ml.cumulants import classify_preview

    try:
        cum = cum if cum is not None else classify_preview(preview, fs)
        if cum.n_symbols == 0:
            return "UNKNOWN", 0.0, "no symbols — sklearn abstains"
        model = get_model()
        row = _sklearn_features(cum, _fm_cv(preview, fs)).reshape(1, -1)
        if not np.all(np.isfinite(row)):
            return "UNKNOWN", 0.0, "non-finite features — sklearn abstains"
        proba = model.predict_proba(row)[0]
        best = int(np.argmax(proba))
        return str(model.classes_[best]), float(proba[best]), ""
    except Exception as exc:
        return "UNKNOWN", 0.0, f"{exc} — sklearn abstains"


@dataclass
class VoteResult:
    winner: str = "UNKNOWN"
    confidence: float = 0.0
    parts: dict = field(default_factory=dict)  # voter -> (mod, conf)
    agreed: bool = False
    note: str = ""


def combine(demod=None, cumulants: CumulantResult | None = None,
            sklearn_vote=("UNKNOWN", 0.0), cnn_vote=("pending", 0.0)) -> VoteResult:
    """Weighted poll. Each part is (modulation, confidence)."""
    parts: dict[str, tuple[str, float]] = {}
    if demod is not None and getattr(demod, "modulation", "UNKNOWN") not in ("UNKNOWN", "pending"):
        parts["demod"] = (demod.modulation, float(min(0.95, max(0.05, demod.margin_db / 12.0))))
    if cumulants is not None and cumulants.modulation != "UNKNOWN":
        parts["cumulants"] = (cumulants.modulation, float(cumulants.confidence))
    if sklearn_vote[0] not in ("UNKNOWN", "pending"):
        parts["sklearn"] = (str(sklearn_vote[0]), float(sklearn_vote[1]))
    if cnn_vote[0] not in ("UNKNOWN", "pending"):
        parts["cnn"] = (str(cnn_vote[0]), float(cnn_vote[1]))
    if not parts:
        return VoteResult(note="all voters abstained")
    scores: dict[str, float] = {}
    for voter, (mod, conf) in parts.items():
        scores[mod] = scores.get(mod, 0.0) + WEIGHTS[voter] * conf
    total = sum(WEIGHTS[v] for v in parts)
    winner = max(scores, key=lambda m: scores[m])
    conf = scores[winner] / total if total > 0 else 0.0
    agreed = len({m for m, _ in parts.values()}) == 1
    demod_mod = getattr(demod, "modulation", None)
    note = f"poll { {v: p for v, p in parts.items()} }"
    if demod_mod not in (None, "UNKNOWN") and winner != demod_mod:
        conf *= 0.7
        note += f" — overrides demod {demod_mod}"
    return VoteResult(
        winner=winner,
        confidence=float(min(0.97, max(0.05, conf))),
        parts=parts, agreed=agreed, note=note,
    )


def vote_log_lines(v: VoteResult) -> list[str]:
    if v.winner == "UNKNOWN":
        return [f"ml vote: UNKNOWN — {v.note}"]
    return [
        f"ml vote: {v.winner} ({v.confidence:.2f}; "
        f"{'all agree' if v.agreed else 'split decision'})",
        v.note,
    ]


def run_ml_vote(preview, fs: int, demod=None):
    """One-call Phase-5 chain. Returns (cumulants, vote, cnn, lines).

    Never raises: every voter degrades to abstain, worst case the vote
    is UNKNOWN and the caller keeps the demod-only view.
    """
    from ml.cnn_onnx import cnn_vote
    from ml.cumulants import CumulantResult, classify_preview

    lines: list[str] = []
    try:
        cum = classify_preview(preview, fs)
    except Exception as exc:
        cum = CumulantResult(note=f"{exc} — cumulants abstain")
    try:
        from ml.cumulants import cumulant_log_lines

        lines += cumulant_log_lines(cum)
    except Exception:
        pass
    sk_mod, sk_conf, sk_note = sklearn_predict(preview, fs, cum)
    if sk_note and "abstains" in sk_note and sk_mod == "UNKNOWN":
        lines.append(f"sklearn: abstain ({sk_note})")
    else:
        lines.append(f"sklearn: {sk_mod} ({sk_conf:.2f}; trained {_TRAIN_SECS:.1f}s one-time)")
    try:
        cnn = cnn_vote(preview, fs)
    except Exception as exc:
        cnn = {"modulation": "pending", "confidence": 0.0, "note": str(exc)}
    lines.append(f"cnn: {cnn['modulation']} — {cnn['note']}")
    v = combine(demod, cum, (sk_mod, sk_conf), (cnn["modulation"], cnn["confidence"]))
    lines += vote_log_lines(v)
    return cum, v, cnn, lines
