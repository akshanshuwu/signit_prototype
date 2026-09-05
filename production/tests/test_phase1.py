"""Phase 1 tests — demo store contract, file validation, ops-console wiring."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_demo_store_loads_all_with_valid_contract():
    from app.demo_store import DEMO_IDS, load_demo, validate_demo

    assert set(DEMO_IDS) == {"bpsk", "qpsk", "qam16", "fsk2"}
    for demo_id in DEMO_IDS:
        demo = load_demo(demo_id)
        assert validate_demo(demo) == [], f"{demo_id} contract violations"


def test_demo_store_shapes():
    from app.demo_store import load_demo

    for demo_id in ("bpsk", "qpsk", "qam16", "fsk2"):
        demo = load_demo(demo_id)
        assert len(demo["psd"]["freqs"]) == 512
        assert len(demo["spectrogram"]["freqs"]) == 128
        assert len(demo["spectrogram"]["times"]) == 64
        assert len(demo["spectrogram"]["z_db"]) == 128
        assert len(demo["constellation"]["i"]) <= 2000
        assert len(demo["bits_preview"]["corr_peak"]["lags"]) == 256


def test_demo_store_rejects_unknown():
    import pytest

    from app.demo_store import load_demo

    with pytest.raises(ValueError, match="Unknown capture"):
        load_demo("badid")


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


def test_mainwindow_opens_all_demos_all_tabs():
    from app.widgets.results_tabs import TAB_ORDER

    win = _make_window()
    try:
        assert win.demo_id == "qpsk"  # default view mirrors web CTA
        for demo_id in ("bpsk", "qpsk", "qam16", "fsk2"):
            assert win.open_demo(demo_id) is True
            assert win.demo_id == demo_id
            assert demo_id.upper() in win.windowTitle()
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


def test_mainwindow_invalid_demo_shows_banner():
    win = _make_window()
    win.show()
    try:
        assert win.open_demo("nope") is False
        assert not win.error_banner.isHidden()
        assert "Unknown capture" in win.error_banner.text()
    finally:
        win.close()


def test_tab_order_matches_web():
    from app.widgets.results_tabs import TAB_ORDER

    assert TAB_ORDER == ("report", "spectrum", "waterfall", "constellation", "compare", "bits")
