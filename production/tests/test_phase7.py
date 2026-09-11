"""Phase 7 tests — auto-chain ticks, XAI, Intel PDF, ROI/impairment re-analysis."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ml.synth import FS, synth


def _make_window():
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import MainWindow

    _app = QApplication.instance() or QApplication([])
    return _app, MainWindow()


def test_tick_line_marks_stages():
    from app.mainwindow import tick_line

    line = tick_line(["ingest", "est", "demod", "vote", "fec"])
    assert all(f"{s} ✓" in line for s in ("ingest", "est", "demod", "vote", "fec"))
    line2 = tick_line(["ingest", "est", "demod"], ["demod"])
    assert "demod ✗" in line2 and "est ✓" in line2


def test_ingest_chain_shows_tick_line(tmp_path):
    _app, win = _make_window()
    try:
        from engine.ingest import ingest_file as _ingest

        x = synth("QPSK", 20.0, 46)
        p = tmp_path / "qpsk.iq"
        x.tofile(p)
        win._on_ingested(_ingest(str(p), fs=FS))
        assert "auto-chain:" in win.mission_log.toPlainText()
    finally:
        win.close()


def test_ingest_shows_tick_line(tmp_path):
    _app, win = _make_window()
    try:
        from engine.ingest import ingest_file as _ingest

        x = synth("BPSK", 20.0, 45)
        p = tmp_path / "bpsk.iq"
        x.tofile(p)
        win._on_ingested(_ingest(str(p), fs=FS))
        text = win.mission_log.toPlainText()
        assert "auto-chain:" in text and "ingest ✓" in text
    finally:
        win.close()


def test_explain_vote_shares():
    from ml.ensemble import combine, run_ml_vote
    from engine.demod import demodulate_preview

    x = synth("QPSK", 20.0, 44)
    demod = demodulate_preview(x, FS)
    _cum, vote, _cnn, _lines = run_ml_vote(x, FS, demod)
    from ml.explain import explain_vote

    lines = explain_vote(vote)
    assert lines and vote.winner in lines[0]
    assert any("voter shares" in line for line in lines)


def test_report_card_shows_explain(tmp_path):
    _app, win = _make_window()
    try:
        from engine.ingest import ingest_file as _ingest

        x = synth("BPSK", 20.0, 45)
        p = tmp_path / "bpsk.iq"
        x.tofile(p)
        win._on_ingested(_ingest(str(p), fs=FS))
        assert win.side_report.explain.text().startswith("AI:")
    finally:
        win.close()


def test_intel_pdf_writes(tmp_path):
    from app.intel_pdf import write_intel_pdf
    from engine.demod import demodulate_preview
    from engine.estimators import analyze_preview, to_demo_dict
    from engine.ingest import IngestResult, ingest_file
    from ml.ensemble import run_ml_vote

    x = synth("QPSK", 20.0, 44)
    p = tmp_path / "qpsk.iq"
    x.tofile(p)
    res = ingest_file(str(p), fs=FS)
    est = analyze_preview(res.preview, FS, 0.0)
    demod = demodulate_preview(res.preview, FS)
    _cum, vote, _cnn, _lines = run_ml_vote(res.preview, FS, demod)
    view = IngestResult(path=str(p), kind="iq", n_samples=len(res.preview),
                        fs=FS, fc=0.0, dtype_label="t", sha256="t",
                        preview=res.preview)
    demo = to_demo_dict(est, view, demod=demod, vote=vote)
    out = str(tmp_path / "intel.pdf")
    write_intel_pdf(demo, out, ["ingest ok", "ml vote: QPSK"])
    with open(out, "rb") as f:
        head = f.read(5)
    assert head == b"%PDF-"
    assert os.path.getsize(out) > 1000


def test_export_pdf_from_window(tmp_path):
    _app, win = _make_window()
    try:
        from engine.ingest import ingest_file as _ingest

        x = synth("QPSK", 20.0, 44)
        p = tmp_path / "qpsk.iq"
        x.tofile(p)
        win._on_ingested(_ingest(str(p), fs=FS))
        out = str(tmp_path / "win.pdf")
        win.export_pdf_to(out)
        assert os.path.getsize(out) > 1000
        with pytest.raises(ValueError):
            from PySide6.QtWidgets import QApplication  # noqa

            from app.mainwindow import MainWindow as MW

            _a = QApplication.instance() or QApplication([])
            w2 = MW()
            w2._demo = None
            try:
                w2.export_pdf_to(str(tmp_path / "empty.pdf"))
            finally:
                w2.close()
    finally:
        win.close()


def test_slice_and_impairments():
    from engine.reanalyze import add_awgn, add_freq_offset, slice_duration_s, slice_preview

    x = synth("QPSK", 20.0, 44)
    dur = slice_duration_s(x, FS)
    assert dur == pytest.approx(len(x) / FS)
    sub = slice_preview(x, FS, 0.0, dur / 2)
    assert len(sub) == len(x) // 2
    with pytest.raises(ValueError):
        slice_preview(x, FS, dur, dur)  # empty
    noisy = add_awgn(x, 12.0)
    assert noisy.shape == x.shape and not np.allclose(noisy, x)
    shifted = add_freq_offset(x, FS, 500.0)
    assert shifted.shape == x.shape and not np.allclose(shifted, x)
    same = add_freq_offset(x, FS, 0.0)
    np.testing.assert_array_equal(same, x)


def test_reanalyze_slice_gui(tmp_path):
    _app, win = _make_window()
    try:
        from engine.ingest import ingest_file as _ingest

        x = synth("QPSK", 20.0, 44)
        p = tmp_path / "qpsk.iq"
        x.tofile(p)
        win._on_ingested(_ingest(str(p), fs=FS))
        assert win.reanalyze(0.0, 0.1) is True
        text = win.mission_log.toPlainText()
        assert "re-analysis" in text and "auto-chain:" in text
        assert "qpsk.iq[0.0-0.1s" in win.windowTitle()
        # impairment probe degrades gracefully (ticks still emitted, no crash)
        assert win.reanalyze(None, None, snr_db=5.0) is True
        assert "auto-chain:" in win.mission_log.toPlainText()
        # nothing ingested -> banner, False
        win._ingest = None
        assert win.reanalyze(0.0, 0.1) is False
        assert not win.error_banner.isHidden()
    finally:
        win.close()


def test_reanalyze_button_wiring(tmp_path):
    _app, win = _make_window()
    try:
        from engine.ingest import ingest_file as _ingest

        x = synth("BPSK", 20.0, 45)
        p = tmp_path / "bpsk.iq"
        x.tofile(p)
        panel = win.file_panel
        panel.check_path(str(p))
        panel.roi_t0.setValue(0.0)
        panel.roi_t1.setValue(0.1)
        panel.reanalyze_btn.click()
        assert "re-analysis" in win.mission_log.toPlainText()
    finally:
        win.close()
