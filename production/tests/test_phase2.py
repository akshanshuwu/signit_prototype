"""Phase 2 tests — ingest engine (memmap, dtypes, wav, hash, GUI wiring)."""
import hashlib
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from engine.ingest import (
    DTYPE_COMPLEX64,
    DTYPE_COMPLEX128,
    DTYPE_INT16,
    IngestError,
    ingest_file,
    log_lines,
    raw_view,
    sha256_stream,
)


@pytest.fixture()
def c64_file(tmp_path):
    rng = np.random.default_rng(0)
    iq = (rng.standard_normal(8192) + 1j * rng.standard_normal(8192)).astype(np.complex64)
    p = tmp_path / "cap.iq"
    iq.tofile(p)
    return str(p), iq


def test_complex64_roundtrip(c64_file):
    path, iq = c64_file
    r = ingest_file(path, fs=48000, fc=0.0, dtype_label=DTYPE_COMPLEX64)
    assert r.n_samples == len(iq)
    assert r.fs == 48000 and r.kind == "iq"
    np.testing.assert_allclose(r.preview, iq[: len(r.preview)], rtol=1e-6)
    assert r.duration_s == pytest.approx(len(iq) / 48000)


def test_int16_scaling(tmp_path):
    raw = (np.arange(8, dtype=np.int16) * 4096).tobytes()
    p = tmp_path / "s16.iq"
    p.write_bytes(raw)
    r = ingest_file(str(p), dtype_label=DTYPE_INT16)
    assert r.n_samples == 4
    expect_i = (np.arange(8, dtype=np.int16)[0::2].astype(np.float32) * 4096) / 32768.0
    np.testing.assert_allclose(r.preview.real, expect_i, rtol=1e-5)


def test_complex128_and_bin(tmp_path):
    iq = (np.arange(16) + 1j * np.arange(16)).astype(np.complex128)
    for name in ("c128.iq", "raw.bin"):
        p = tmp_path / name
        iq.tofile(p)
        r = ingest_file(str(p), dtype_label=DTYPE_COMPLEX128)
        assert r.n_samples == 16
        np.testing.assert_allclose(r.preview.real, np.arange(16, dtype=np.float32)[: len(r.preview)])


def test_odd_size_rejected(tmp_path):
    p = tmp_path / "odd.iq"
    p.write_bytes(b"\x00" * 10)  # not a multiple of 8
    with pytest.raises(IngestError, match="multiple of 8"):
        ingest_file(str(p), dtype_label=DTYPE_COMPLEX64)


def test_unsupported_and_missing():
    with pytest.raises(IngestError, match="isn't supported"):
        ingest_file("/tmp/nope.exe")
    with pytest.raises(IngestError, match="could not be read"):
        ingest_file("/tmp/does-not-exist.iq")


def test_sha256_and_log_lines(c64_file):
    path, iq = c64_file
    r = ingest_file(path)
    assert sha256_stream(path) == hashlib.sha256(open(path, "rb").read()).hexdigest()
    lines = log_lines(r)
    assert lines[0].startswith("ingest ok: 8192 samples @ 48000 Hz")
    assert lines[1].startswith("sha256: ")


def test_large_raw_uses_memmap(tmp_path):
    n = 3_000_000  # 24 MB complex64 — over old 15MB cap, must not fully load
    p = tmp_path / "big.iq"
    np.zeros(n, dtype=np.complex64).tofile(p)
    r = ingest_file(str(p))
    assert r.n_samples == n
    assert len(r.preview) <= 262_144
    view = raw_view(str(p), DTYPE_COMPLEX64)
    assert len(view) == n
    assert isinstance(view, np.memmap)


def test_wav_mono_and_stereo(tmp_path):
    pytest.importorskip("scipy.io.wavfile")
    from scipy.io import wavfile

    mono = (np.linspace(-1, 1, 8000) * 30000).astype(np.int16)
    pm = tmp_path / "m.wav"
    wavfile.write(pm, 16000, mono)
    rm = ingest_file(str(pm), fs=48000)
    assert rm.kind == "wav" and rm.fs == 16000 and rm.n_samples == 8000
    assert np.allclose(rm.preview.imag, 0)

    stereo = np.stack([mono, -mono], axis=1)
    ps = tmp_path / "s.wav"
    wavfile.write(ps, 44100, stereo)
    rs = ingest_file(str(ps))
    assert rs.fs == 44100
    np.testing.assert_allclose(rs.preview.real, -rs.preview.imag, rtol=1e-4)


def _make_panel():
    from PySide6.QtWidgets import QApplication

    from app.widgets.file_panel import FilePanel

    _app = QApplication.instance() or QApplication([])
    return FilePanel()


def test_file_panel_end_to_end(c64_file):
    path, _ = c64_file
    panel = _make_panel()
    seen = []
    panel.file_ingested.connect(seen.append)
    msg = panel.check_path(path)
    assert "8192 samples @ 48000 Hz" in msg
    assert len(seen) == 1 and seen[0].n_samples == 8192
    assert "sha256" in panel.validation_msg.text()


def test_file_panel_rejections(tmp_path):
    panel = _make_panel()
    bad = tmp_path / "x.exe"
    bad.write_bytes(b"nope")
    assert "isn't supported" in panel.check_path(str(bad))
    assert "could not be read" in panel.check_path(str(tmp_path / "ghost.iq"))


def test_mainwindow_ingest_updates_log(c64_file):
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import MainWindow
    from engine.ingest import ingest_file as _ingest

    _app = QApplication.instance() or QApplication([])
    win = MainWindow()
    try:
        path, _ = c64_file
        win._on_ingested(_ingest(path))
        text = win.mission_log.toPlainText()
        assert "ingest ok: 8192 samples" in text and "sha256:" in text
    finally:
        win.close()
