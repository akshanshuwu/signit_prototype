"""Phase 1 tests — result contract, file validation, window wiring.

File ingest is the only analysis path. Contract checks run against live
ingest -> chain -> to_demo_dict results (temp .iq files), never bundles.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _live_demo(tmp_path, mod="QPSK", seed=44):
    from engine.ingest import ingest_file
    from ml.synth import FS, synth

    p = tmp_path / f"{mod.lower()}.iq"
    synth(mod, 20.0, seed).tofile(p)
    from engine.demod import demodulate_preview
    from engine.estimators import analyze_preview, to_demo_dict
    from ml.ensemble import run_ml_vote

    preview = ingest_file(str(p), fs=FS).preview
    est = analyze_preview(preview, FS, 0.0)
    from engine.ingest import IngestResult

    demod = demodulate_preview(preview, FS)
    _cum, vote, _cnn, _lines = run_ml_vote(preview, FS, demod)
    view = IngestResult(path=str(p), kind="iq", n_samples=len(preview),
                        fs=FS, fc=0.0, dtype_label="t", sha256="t",
                        preview=preview)
    return to_demo_dict(est, view, demod=demod, vote=vote)


def test_live_results_have_valid_contract(tmp_path):
    from app.demo_store import validate_demo

    for mod in ("BPSK", "QPSK", "16QAM", "2FSK"):
        demo = _live_demo(tmp_path, mod)
        assert validate_demo(demo) == [], f"{mod} contract violations"


def test_live_result_shapes(tmp_path):
    demo = _live_demo(tmp_path)
    assert len(demo["psd"]["freqs"]) == 512
    assert len(demo["spectrogram"]["freqs"]) == 128
    assert len(demo["spectrogram"]["times"]) == 64
    assert len(demo["spectrogram"]["z_db"]) == 128
    assert len(demo["constellation"]["i"]) <= 2000
    assert len(demo["bits_preview"]["corr_peak"]["lags"]) == 256


def test_file_validation_messages():
    from app.widgets.file_panel import validate_file

    assert "isn't supported" in validate_file("sig.exe", 100)
    big = validate_file("big.iq", 3 * 1024 * 1024 * 1024)
    assert "2 GB" in big and "3072.0 MB" in big
    assert "passed validation" in validate_file("cap.iq", 100)


def _make_window():
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import MainWindow

    _app = QApplication.instance() or QApplication([])
    return MainWindow()


def test_mainwindow_ingest_renders_all_tabs(tmp_path):
    from engine.ingest import ingest_file
    from ml.synth import FS, synth
    from app.widgets.results_tabs import TAB_ORDER

    win = _make_window()
    try:
        assert win._demo is None  # empty drop-prompt startup, no auto demo
        assert "drop any" in win.mission_log.toPlainText().lower()
        for mod in ("BPSK", "QPSK", "16QAM", "2FSK"):
            p = tmp_path / f"{mod.lower()}.iq"
            synth(mod, 20.0, 44).tofile(p)
            win._on_ingested(ingest_file(str(p), fs=FS))
            assert win._source == "live"
            assert f"{mod.lower()}.iq" in win.windowTitle()
            for index in range(len(TAB_ORDER)):
                win.results_tabs.setCurrentIndex(index)
                assert win.results_tabs.tab_id(index) == TAB_ORDER[index]
            # report + log populated
            assert win.side_report.mod_label.text() != "—"
            assert "$" in win.mission_log.toPlainText()
            # bits + comparator populated
            assert len(win.results_tabs.bits.hex_view.toPlainText()) > 0
            assert "dB" in win.results_tabs.comparator.iq_value.text()
    finally:
        win.close()


def test_empty_export_raises():
    import pytest

    win = _make_window()
    try:
        with pytest.raises(ValueError):
            win.export_pdf_to("nowhere.pdf")
    finally:
        win.close()


def test_tab_order_matches_web():
    from app.widgets.results_tabs import TAB_ORDER

    assert TAB_ORDER == ("report", "spectrum", "waterfall", "constellation", "compare", "bits")
