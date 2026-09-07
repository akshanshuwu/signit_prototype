"""Hardening tests — large-file scale, degenerate inputs, chain-of-custody.

M4: proves memmap ingest stays bounded on large captures, the chain never
leaves the console blank on garbage, and hashes pin file identity.
"""
import os
import sys
import time

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from engine.ingest import ingest_file, raw_view, sha256_stream


def test_large_file_stays_bounded(tmp_path):
    n = 32_000_000  # 256 MB complex64 — well past any load-it-all cap
    p = tmp_path / "large.iq"
    np.zeros(n, dtype=np.complex64).tofile(p)
    t0 = time.time()
    r = ingest_file(str(p))
    dt = time.time() - t0
    assert r.n_samples == n
    assert len(r.preview) <= 262_144
    assert isinstance(raw_view(str(p), "complex64 (I/Q interleaved float32)"), np.memmap)
    assert dt < 60, f"ingest took {dt:.1f}s — chunked path regressed"


def test_hash_pins_identity(tmp_path):
    p = tmp_path / "cap.iq"
    rng = np.random.default_rng(0)
    iq = (rng.standard_normal(4096) + 1j * rng.standard_normal(4096)).astype(np.complex64)
    iq.tofile(p)
    h1 = sha256_stream(str(p))
    assert sha256_stream(str(p)) == h1  # stable across reads
    assert ingest_file(str(p)).sha256 == h1  # ingest reports the same digest
    with open(p, "r+b") as f:  # one flipped byte -> new identity
        f.seek(100)
        f.write(b"\xFF")
    assert sha256_stream(str(p)) != h1


def _make_window():
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import MainWindow

    _app = QApplication.instance() or QApplication([])
    return MainWindow()


def test_zeros_file_never_blank(tmp_path):
    p = tmp_path / "zeros.iq"
    np.zeros(8192, dtype=np.complex64).tofile(p)
    win = _make_window()
    try:
        from engine.ingest import ingest_file as _ingest

        win._on_ingested(_ingest(str(p)))
        text = win.mission_log.toPlainText()
        assert "auto-chain:" in text  # ticks emitted even on total failure
        assert "demod ✗" in text
        assert win.error_banner.isHidden()  # estimator-only view, not an error state
        assert win.side_report.mod_label.text() == "UNKNOWN"
    finally:
        win.close()


def test_noise_file_honest_unknown(tmp_path):
    rng = np.random.default_rng(3)
    noise = (rng.standard_normal(32768) + 1j * rng.standard_normal(32768)).astype(np.complex64)
    p = tmp_path / "noise.iq"
    noise.tofile(p)
    win = _make_window()
    try:
        from engine.ingest import ingest_file as _ingest

        win._on_ingested(_ingest(str(p)))
        assert win.side_report.mod_label.text() == "UNKNOWN"
        assert "auto-chain:" in win.mission_log.toPlainText()
    finally:
        win.close()


def test_empty_file_rejected_gracefully(tmp_path):
    p = tmp_path / "empty.iq"
    p.write_bytes(b"")
    win = _make_window()
    try:
        msg = win.file_panel.check_path(str(p))
        assert msg  # some message shown, no exception
        assert "passed validation" not in msg or "0 samples" in msg or "empty" in msg.lower()
    finally:
        win.close()
