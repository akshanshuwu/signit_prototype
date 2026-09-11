"""Phase 0 smoke tests — package imports + window shell contract."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_packages_importable():
    import app  # noqa: F401
    import engine  # noqa: F401
    import ml  # noqa: F401


def test_mainwindow_contract():
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import APP_OBJECT_NAME, APP_TITLE, MainWindow

    _app = QApplication.instance() or QApplication([])
    win = MainWindow()
    try:
        assert win.objectName() == APP_OBJECT_NAME
        assert APP_TITLE in win.windowTitle()
        assert win.findChild(object, "mainSplitter") is not None
        assert win.findChild(object, "filePanel") is not None
        assert win.findChild(object, "resultsTabs") is not None
        assert win.findChild(object, "missionLog") is not None
        assert win.width() >= 1000 and win.height() >= 600
        # Fullscreen contract: center tabs take extra width (stretch set
        # in MainWindow), sidebars keep minimums, center never collapses.
        splitter = win.findChild(object, "mainSplitter")
        assert not splitter.isCollapsible(1)
        assert win.file_panel.minimumWidth() >= 220
        assert win.side_report.minimumWidth() >= 240
        assert win.minimumWidth() >= 1000 and win.minimumHeight() >= 600
    finally:
        win.close()
