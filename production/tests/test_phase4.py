"""Phase 4 tests — real demod on synthesized captures (no mocks for DSP)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from engine.demod import (
    DemodError,
    demodulate_preview,
    estimate_carrier,
    estimate_symbol_rate,
    sync_search,
)

FS = 48000
RATE = 2000
SPS = FS // RATE
N_SYM = 1200  # 28800 samples — small but exercises the full chain


def _channel(x, snr_db=20, freq_offset=200.0, seed=0):
    rng = np.random.default_rng(seed)
    sig_pwr = float(np.mean(np.abs(x) ** 2))
    noise_pwr = sig_pwr / (10.0 ** (snr_db / 10.0))
    noise = (rng.standard_normal(len(x)) + 1j * rng.standard_normal(len(x)))
    noise = noise * np.sqrt(noise_pwr / 2.0)
    t = np.arange(len(x)) / FS
    return ((x + noise) * np.exp(2j * np.pi * freq_offset * t)).astype(np.complex64)


def _rect(symbols):
    return np.repeat(symbols, SPS).astype(np.complex64)


def synth_bpsk(seed=0):
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, N_SYM).astype(np.uint8)
    return _channel(_rect(np.where(bits, 1.0, -1.0).astype(np.complex64))), bits


def synth_qpsk(seed=1):
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, 2 * N_SYM).astype(np.uint8)
    i = 2 * bits[0::2].astype(np.int16) - 1
    q = 2 * bits[1::2].astype(np.int16) - 1
    sym = (i + 1j * q) / np.sqrt(2.0)
    return _channel(_rect(sym.astype(np.complex64))), bits


_LEVELS = np.array([-3.0, -1.0, 1.0, 3.0]) / np.sqrt(10.0)


def synth_qam16(seed=2):
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, 4 * N_SYM).astype(np.uint8)
    ri = bits[0::4] * 2 + bits[1::4]
    qi = bits[2::4] * 2 + bits[3::4]
    sym = _LEVELS[ri] + 1j * _LEVELS[qi]
    return _channel(_rect(sym.astype(np.complex64))), bits


def synth_fsk2(dev=2000.0, seed=3):
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, N_SYM).astype(np.uint8)
    freqs = np.where(bits, dev, -dev)
    phase = 2.0 * np.pi * np.cumsum(np.repeat(freqs, SPS)) / FS
    return _channel(np.exp(1j * phase).astype(np.complex64)), bits


def _ber(a: np.ndarray, b: np.ndarray) -> float:
    n = min(len(a), len(b))
    return float(np.mean(a[:n] != b[:n]))


def test_carrier_estimate():
    t = np.arange(32768) / FS
    tone = np.exp(2j * np.pi * 5000 * t).astype(np.complex64)
    assert abs(estimate_carrier(tone, FS) - 5000) < 50


def test_symbol_rate_estimate_psk():
    x, _ = synth_bpsk()
    rate, _method = estimate_symbol_rate(x, FS)
    assert rate == pytest.approx(RATE, rel=0.1)


def test_bpsk_demod():
    x, bits = synth_bpsk()
    d = demodulate_preview(x, FS)
    assert d.modulation == "BPSK", d.candidates
    assert d.symbol_rate == pytest.approx(RATE, rel=0.1)
    assert min(_ber(d.bits, bits), _ber(d.bits, 1 - bits)) < 0.05
    assert d.evm_db < -10


def test_qpsk_demod():
    x, bits = synth_qpsk()
    d = demodulate_preview(x, FS)
    assert d.modulation == "QPSK", d.candidates
    assert d.symbol_rate == pytest.approx(RATE, rel=0.1)
    # 90° phase ambiguity: compare decoded symbols up to 4 rotations.
    bi = 2 * bits[0::2].astype(np.int16) - 1
    bq = 2 * bits[1::2].astype(np.int16) - 1
    tx = (bi + 1j * bq) / np.sqrt(2.0)
    ri = 2 * d.bits[0::2].astype(np.int16) - 1
    rq = 2 * d.bits[1::2].astype(np.int16) - 1
    rx = (ri + 1j * rq) / np.sqrt(2.0)
    n = min(len(tx), len(rx))
    errs = [np.mean(np.abs(rx[:n] - tx[:n] * np.exp(1j * k * np.pi / 2)) ** 2) for k in range(4)]
    assert min(errs) < 0.1


def test_qam16_demod():
    x, _bits = synth_qam16()
    d = demodulate_preview(x, FS)
    assert d.modulation == "16QAM", d.candidates
    assert d.symbol_rate == pytest.approx(RATE, rel=0.1)
    assert d.evm_db < -10


def test_fsk_demod():
    x, bits = synth_fsk2()
    d = demodulate_preview(x, FS)
    assert d.modulation == "2FSK", d.candidates
    assert d.symbol_rate == pytest.approx(RATE, rel=0.15)
    assert _ber(d.bits, bits) < 0.05


def test_sync_finder_barker():
    from engine.demod import PREAMBLES

    rng = np.random.default_rng(7)
    pre = np.array(PREAMBLES["BARKER13"], dtype=np.uint8)
    bits = np.concatenate([pre, rng.integers(0, 2, 2000).astype(np.uint8)])
    sym = np.where(bits, 1.0, -1.0).astype(np.complex64)
    d = demodulate_preview(_channel(_rect(sym), seed=7), FS)
    name, lag, val, _lags, _vals = sync_search((d.bits > 0).astype(np.uint8))
    assert name == "BARKER13"
    assert lag == 0
    assert abs(val) > 0.9


def test_noise_is_unknown():
    rng = np.random.default_rng(9)
    noise = (rng.standard_normal(32768) + 1j * rng.standard_normal(32768)).astype(np.complex64)
    d = demodulate_preview(noise, FS)
    assert d.modulation == "UNKNOWN"


def test_empty_and_bad_fs_rejected():
    with pytest.raises(DemodError):
        demodulate_preview(np.zeros(0, dtype=np.complex64), FS)
    with pytest.raises(DemodError):
        demodulate_preview(np.ones(1024, dtype=np.complex64), 0)


def test_demo_dict_carries_demod(tmp_path):
    from app.demo_store import validate_demo
    from engine.estimators import analyze_preview, to_demo_dict
    from engine.ingest import ingest_file

    x, _ = synth_bpsk()
    p = tmp_path / "bpsk.iq"
    x.tofile(p)
    ing = ingest_file(str(p), fs=FS)
    est = analyze_preview(ing.preview, ing.fs, ing.fc)
    d = demodulate_preview(ing.preview, ing.fs)
    demo = to_demo_dict(est, ing, demod=d)
    assert validate_demo(demo) == []
    assert demo["predictions"]["modulation"] == "BPSK"
    assert demo["predictions"]["symbol_rate_est"] == pytest.approx(RATE, rel=0.1)
    assert demo["predictions"]["confidence"] > 0
    assert len(demo["bits_preview"]["hex"]) > 0


def test_mainwindow_ingest_shows_demod(tmp_path):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import MainWindow
    from engine.ingest import ingest_file as _ingest

    _app = QApplication.instance() or QApplication([])
    x, _ = synth_bpsk()
    p = tmp_path / "bpsk.iq"
    x.tofile(p)
    win = MainWindow()
    try:
        win._on_ingested(_ingest(str(p), fs=FS))
        assert win.side_report.mod_label.text() == "BPSK"
        text = win.mission_log.toPlainText()
        assert "demod: BPSK" in text
        assert win.error_banner.isHidden()
    finally:
        win.close()
