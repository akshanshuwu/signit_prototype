"""F3 tests — prove the .exe path is live, not hardcoded.

- Empty startup (no auto demo).
- Synthetic references run the real chain without touching bundled JSONs.
- Real file ingest records local history.
- Fallback demos remain valid but are explicitly fallback.
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
        assert win.demo_id is None
        assert win._demo is None
        assert win._source == "empty"
        assert "drop any" in win.mission_log.toPlainText().lower()
        assert win.side_report.mod_label.text() == "UNKNOWN"
    finally:
        win.close()


def test_synth_chain_no_demo_files(tmp_path):
    """Live path must never call load_demo (block it outright)."""
    import app.mainwindow as mw
    from app.demo_store import validate_demo

    _app, win = _make_window(history_db=str(tmp_path / "h.db"))
    try:
        def _boom(demo_id):
            raise AssertionError("load_demo called in live path!")

        old, mw.load_demo = mw.load_demo, _boom
        try:
            for key in ("bpsk", "qpsk", "qam16", "fsk2"):
                assert win.open_synthetic_reference(key) is True
                assert win._demo is not None
                assert validate_demo(win._demo) == [], f"{key} live dict invalid"
                assert win._source == "synth"
                assert "auto-chain:" in win.mission_log.toPlainText()
        finally:
            mw.load_demo = old
    finally:
        win.close()


def test_synth_rejects_unknown():
    _app, win = _make_window()
    try:
        assert win.open_synthetic_reference("nope") is False
        assert not win.error_banner.isHidden()
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


def test_fallback_demos_still_valid():
    from app.demo_store import DEMO_IDS, load_demo, validate_demo

    _app, win = _make_window()
    try:
        for demo_id in DEMO_IDS:
            assert validate_demo(load_demo(demo_id)) == []
        assert win.open_demo("qpsk") is True
        assert win._source == "fallback"
        assert "fallback: bundled" in win.mission_log.toPlainText()
    finally:
        win.close()
