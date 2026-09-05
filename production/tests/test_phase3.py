"""Phase 3 tests — real estimators on ingest previews (no mocks for DSP)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from engine.estimators import (
    EstimatorError,
    analyze_preview,
    compute_psd,
    compute_spectrogram,
    estimate_snr_bw,
    to_demo_dict,
)
from engine.ingest import ingest_file


def _tone(fs=48000, f0=5000, n=32768, snr_db=30):
    rng = np.random.default_rng(1)
    t = np.arange(n) / fs
    sig = np.exp(2j * np.pi * f0 * t).astype(np.complex64)
    sig_pwr = np.mean(np.abs(sig) ** 2)
    noise_pwr = sig_pwr / (10.0 ** (snr_db / 10.0))
    noise = (rng.standard_normal(n) + 1j * rng.standard_normal(n)) * np.sqrt(noise_pwr / 2)
    return (sig + noise).astype(np.complex64)


def test_psd_shape_and_centered():
    x = _tone()
    freqs, mags = compute_psd(x, 48000)
    assert freqs.shape == (512,) and mags.shape == (512,)
    assert freqs[0] == pytest.approx(-24000.0)
    assert freqs[-1] == pytest.approx(24000.0)
    assert np.all(np.isfinite(mags))


def test_tone_peak_detected():
    x = _tone(f0=5000)
    freqs, mags = compute_psd(x, 48000)
    snr, bw, peak = estimate_snr_bw(freqs, mags)
    assert abs(peak - 5000) < 1500  # Welch bin + interp tolerance
    assert snr > 10
    assert 0 < bw < 24000


def test_tone_snr_above_noise():
    tone = _tone(snr_db=30)
    rng = np.random.default_rng(2)
    noise = (rng.standard_normal(32768) + 1j * rng.standard_normal(32768)).astype(np.complex64)
    snr_tone, _, _ = estimate_snr_bw(*compute_psd(tone, 48000))
    snr_noise, _, _ = estimate_snr_bw(*compute_psd(noise, 48000))
    assert snr_tone > snr_noise + 5


def test_spectrogram_shape():
    x = _tone()
    times, freqs, z = compute_spectrogram(x, 48000)
    assert times.shape == (64,) and freqs.shape == (128,) and z.shape == (128, 64)
    assert np.all(np.isfinite(z))


def test_analyze_preview_end_to_end(tmp_path):
    iq = _tone(n=16384)
    p = tmp_path / "tone.iq"
    iq.tofile(p)
    ing = ingest_file(str(p), fs=48000, fc=1000.0)
    est = analyze_preview(ing.preview, ing.fs, ing.fc)
    assert len(est.const_i) <= 2000 and len(est.const_i) > 100
    assert len(est.corr_lags) == 256 and len(est.corr_vals) == 256
    assert est.hex_text and est.ascii_text
    assert abs(est.peak_freq - 5000) < 1500
    demo = to_demo_dict(est, ing)
    from app.demo_store import validate_demo

    assert validate_demo(demo) == []
    assert demo["meta"]["file"] == "tone.iq"
    assert demo["meta"]["fs"] == 48000
    assert demo["predictions"]["modulation"] == "UNKNOWN"  # classifier is a later phase
    assert len(demo["psd"]["freqs"]) == 512


def test_empty_and_bad_fs_rejected():
    with pytest.raises(EstimatorError):
        analyze_preview(np.zeros(0, dtype=np.complex64), 48000)
    with pytest.raises(EstimatorError):
        analyze_preview(np.ones(1024, dtype=np.complex64), 0)


def test_mainwindow_ingest_renders_plots():
    PySide6 = pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication  # noqa: F401

    from app.mainwindow import MainWindow
    from engine.ingest import ingest_file as _ingest

    _app = QApplication.instance() or QApplication([])
    win = MainWindow()
    try:
        rng = np.random.default_rng(3)
        n = 8192
        t = np.arange(n) / 48000
        iq = (np.exp(2j * np.pi * 3000 * t) + 0.1 * (rng.standard_normal(n) + 1j * rng.standard_normal(n))).astype(np.complex64)
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".iq", delete=False) as f:
            iq.tofile(f.name)
            path = f.name
        res = _ingest(path, fs=48000)
        win._on_ingested(res)
        text = win.mission_log.toPlainText()
        assert "ingest ok" in text and "psd ok" in text
        # Report shows measured file, spectrum tab holds 512 real points.
        assert "tone" not in win.side_report.mod_label.text()  # UNKNOWN until classifier
        assert win.side_report.mod_label.text() == "UNKNOWN"
        assert win.error_banner.isHidden()
    finally:
        win.close()
