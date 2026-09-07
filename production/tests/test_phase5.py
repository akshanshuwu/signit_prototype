"""Phase 5 tests — cumulant classifier + sklearn ensemble + ONNX hook."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ml.cumulants import (
    THEORY,
    classify_features,
    classify_preview,
    cumulant_features,
)
from ml.synth import CLASSES, FS, synth


def _ideal(mod: str, n: int = 4000):
    rng = np.random.default_rng(0)
    if mod == "BPSK":
        return np.where(rng.integers(0, 2, n), 1.0, -1.0).astype(np.complex64)
    if mod == "QPSK":
        b = rng.integers(0, 2, 2 * n).astype(np.int16)
        return (((2 * b[0::2] - 1) + 1j * (2 * b[1::2] - 1)) / np.sqrt(2.0)).astype(np.complex64)
    if mod == "16QAM":
        lv = np.array([-3.0, -1.0, 1.0, 3.0]) / np.sqrt(10.0)
        b = rng.integers(0, 2, 4 * n).astype(np.int16)
        return (lv[b[0::4] * 2 + b[1::4]] + 1j * lv[b[2::4] * 2 + b[3::4]]).astype(np.complex64)
    # 2FSK: constant-envelope phasor with random walk phase (moment-equivalent)
    ph = np.cumsum(rng.standard_normal(n) * 0.5)
    return np.exp(1j * ph).astype(np.complex64)


def test_theory_values_on_ideal_symbols():
    for mod in CLASSES:
        feat = cumulant_features(_ideal(mod))
        thy = np.array(THEORY[mod])
        assert np.allclose(feat, thy, atol=0.08), f"{mod}: {feat} vs {thy}"
        res = classify_features(feat)
        assert res.modulation == mod
        assert res.confidence > 0.5


def _seed(mod: str, base: int, span: int) -> int:
    """Deterministic per-mod seed (built-in hash() is salted per process)."""
    return base + sum(mod.encode()) % span


def test_classify_preview_noisy():
    for mod in CLASSES:
        x = synth(mod, 20.0, _seed(mod, 500, 97))
        res = classify_preview(x, FS)
        assert res.modulation == mod, f"{mod}: {res.ranking} ({res.note})"
        assert res.n_symbols > 0


def test_noise_abstains():
    rng = np.random.default_rng(11)
    noise = (rng.standard_normal(32768) + 1j * rng.standard_normal(32768)).astype(np.complex64)
    res = classify_preview(noise, FS)
    assert res.modulation == "UNKNOWN" or res.confidence < 0.3


def test_empty_and_bad_fs_rejected():
    from ml.cumulants import CumulantError

    with pytest.raises(CumulantError):
        classify_preview(np.zeros(0, dtype=np.complex64), FS)
    with pytest.raises(CumulantError):
        classify_preview(np.ones(1024, dtype=np.complex64), 0)


def test_sklearn_deterministic_and_accurate():
    from ml.ensemble import sklearn_predict

    x = synth("QPSK", 12.0, 777)
    a = sklearn_predict(x, FS)
    b = sklearn_predict(x, FS)
    assert a[0] == b[0] and a[1] == pytest.approx(b[1])
    # Held-out seeds ( differ from training seeds ) across all classes.
    good = 0
    for mod in CLASSES:
        pred, _conf, _note = sklearn_predict(synth(mod, 12.0, _seed(mod, 900, 89)), FS)
        good += pred == mod
    assert good >= 3, f"sklearn held-out accuracy too low: {good}/4"


def test_combine_override_and_abstain():
    from ml.ensemble import combine

    class _D:
        modulation = "BPSK"
        margin_db = 9.0

    class _C:
        modulation = "QPSK"
        confidence = 0.9

    v = combine(_D(), _C(), ("QPSK", 0.8), ("pending", 0.0))
    assert v.winner == "QPSK"
    assert "overrides demod BPSK" in v.note
    assert v.confidence < 0.9  # tempered
    v2 = combine(None, None, ("UNKNOWN", 0.0), ("pending", 0.0))
    assert v2.winner == "UNKNOWN"


def test_cnn_votes_with_model():
    from ml.cnn_onnx import cnn_vote, model_path

    assert os.path.isfile(model_path())  # produced by ml/train_cnn.py (Phase 6)
    x = synth("BPSK", 20.0, 42)
    vote = cnn_vote(x, FS)
    assert vote["modulation"] in CLASSES and vote["confidence"] > 0.0


def test_cnn_pending_without_model_file(monkeypatch):
    import ml.cnn_onnx as cnn_module

    monkeypatch.setattr(cnn_module, "model_path", lambda: "/nonexistent/signit_cnn.onnx")
    x = synth("BPSK", 20.0, 42)
    vote = cnn_module.cnn_vote(x, FS)
    assert vote["modulation"] == "pending" and vote["confidence"] == 0.0


def test_lone_cnn_abstains():
    from ml.ensemble import combine

    v = combine(None, None, ("UNKNOWN", 0.0), ("BPSK", 0.9))
    assert v.winner == "UNKNOWN"
    assert "uncorroborated" in v.note


def test_train_cnn_stub_when_no_torch():
    import importlib.util

    if importlib.util.find_spec("torch") is not None:
        pytest.skip("torch installed — training covered in Phase 6 CI")
    from ml.train_cnn import main

    assert main() == 2


def test_constellation_image_contract():
    from ml.cnn_onnx import constellation_image

    x = synth("16QAM", 20.0, 43)
    img = constellation_image(x)
    assert img.shape == (1, 1, 64, 64) and img.dtype == np.float32
    assert 0.0 <= img.min() and img.max() <= 1.0


def test_demo_dict_carries_vote(tmp_path):
    from app.demo_store import validate_demo
    from engine.demod import demodulate_preview
    from engine.estimators import analyze_preview, to_demo_dict
    from engine.ingest import ingest_file
    from ml.ensemble import run_ml_vote

    x = synth("QPSK", 20.0, 44)
    p = tmp_path / "qpsk.iq"
    x.tofile(p)
    ing = ingest_file(str(p), fs=FS)
    est = analyze_preview(ing.preview, ing.fs, ing.fc)
    demod = demodulate_preview(ing.preview, ing.fs)
    _cum, v, _cnn, _lines = run_ml_vote(ing.preview, ing.fs, demod)
    demo = to_demo_dict(est, ing, demod=demod, vote=v)
    assert validate_demo(demo) == []
    assert demo["predictions"]["modulation"] == v.winner == "QPSK"
    assert demo["predictions"]["confidence"] > 0
    assert "QPSK" in demo["predictions"]["votes"]["cumulants"]
    assert demo["predictions"]["votes"]["CNN"] >= 0.0  # model now trained; >= 0 always


def test_mainwindow_ingest_shows_vote(tmp_path):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import MainWindow
    from engine.ingest import ingest_file as _ingest

    _app = QApplication.instance() or QApplication([])
    x = synth("BPSK", 20.0, 45)
    p = tmp_path / "bpsk.iq"
    x.tofile(p)
    win = MainWindow()
    try:
        win._on_ingested(_ingest(str(p), fs=FS))
        assert win.side_report.mod_label.text() != "—"
        text = win.mission_log.toPlainText()
        assert "ml vote:" in text and "cumulants:" in text
        assert win.error_banner.isHidden()
    finally:
        win.close()
