"""Live-chain tests — prove the .exe path is measured file ingest.

- Empty startup (no auto content).
- Temp .iq files through ingest + full chain validate and record history.
- File ingest is the only path: no sample buttons, no bundled demos.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_window(history_db=None):
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import MainWindow

    _app = QApplication.instance() or QApplication([])
    return _app, MainWindow(history_db=history_db)


def test_empty_startup():
    _app, win = _make_window()
    try:
        assert win._demo is None
        assert win._source == "empty"
        assert "drop any" in win.mission_log.toPlainText().lower()
        assert win.side_report.mod_label.text() == "UNKNOWN"
    finally:
        win.close()


def test_file_chain_validates_all_mods(tmp_path):
    """Temp .iq files (one per modulation) validate through the real chain."""
    from app.demo_store import validate_demo
    from engine.ingest import ingest_file
    from ml.synth import FS, synth

    _app, win = _make_window(history_db=str(tmp_path / "h.db"))
    try:
        for mod in ("BPSK", "QPSK", "16QAM", "2FSK"):
            p = tmp_path / f"{mod.lower()}.iq"
            synth(mod, 20.0, 44).tofile(p)
            win._on_ingested(ingest_file(str(p), fs=FS))
            assert win._demo is not None
            assert validate_demo(win._demo) == [], f"{mod} live dict invalid"
            assert win._source == "live"
            assert "auto-chain:" in win.mission_log.toPlainText()
    finally:
        win.close()


def test_no_sample_or_demo_entry_points():
    """Fresh app: no synth buttons, no demo loader on the window or panel."""
    _app, win = _make_window()
    try:
        assert not hasattr(win, "open_synthetic_reference")
        assert not hasattr(win, "open_demo")
        assert not hasattr(win, "demo_id")
        assert not hasattr(win.file_panel, "sample_selected")
        assert len(win.file_panel.findChildren(object, "samplesGroup")) == 0
    finally:
        win.close()


def test_file_ingest_records_history(tmp_path):
    from engine.history import list_runs
    from engine.ingest import ingest_file
    from ml.synth import FS, synth

    _app, win = _make_window(history_db=str(tmp_path / "hist.db"))
    try:
        p = tmp_path / "cap.iq"
        synth("QPSK", 20.0, 44).tofile(p)
        win._on_ingested(ingest_file(str(p), fs=FS))
        assert win._source == "live"
        rows = list_runs(str(tmp_path / "hist.db"))
        assert len(rows) == 1
        assert rows[0]["filename"] == "cap.iq"
        assert rows[0]["modulation"] == win._demo["predictions"]["modulation"]
    finally:
        win.close()
