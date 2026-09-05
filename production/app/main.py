"""SIGNIT entry point — native Windows .exe (PyInstaller target).

Run (dev):  python3 -m app.main        (from production/)
Smoke (headless CI / macOS without display):
            QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke
"""
from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication) -> str:
    """Apply Qt-Material Dark theme if available, else minimal dark fallback.

    Returns the theme name applied ("qt-material-dark" or "fallback-dark").
    """
    try:
        from qt_material import apply_stylesheet

        apply_stylesheet(app, theme="dark_teal.xml")
        return "qt-material-dark"
    except Exception:
        app.setStyleSheet("QMainWindow { background: #020617; } QLabel { color: #e2e8f0; }")
        return "fallback-dark"


def create_app(argv: list[str] | None = None) -> QApplication:
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("SIGNIT")
    app.setOrganizationName("SIGNIT")
    apply_theme(app)
    return app


def main(argv: list[str] | None = None) -> int:
    from app.mainwindow import MainWindow

    parser = argparse.ArgumentParser(prog="SIGNIT")
    parser.add_argument("--smoke", action="store_true", help="open and immediately close (headless check)")
    args = parser.parse_args(argv)

    app = create_app(sys.argv if argv is None else [sys.argv[0], *argv] if argv else sys.argv)
    win = MainWindow()
    win.show()
    if args.smoke:
        # Phase 1 smoke: cycle every demo through every tab offscreen.
        from app.demo_store import DEMO_IDS

        from app.widgets.results_tabs import TAB_ORDER

        app.processEvents()
        for demo_id in DEMO_IDS:
            ok = win.open_demo(demo_id)
            app.processEvents()
            for index in range(len(TAB_ORDER)):
                win.results_tabs.setCurrentIndex(index)
                app.processEvents()
            print(f"SMOKE demo={demo_id} ok={ok} tabs={len(TAB_ORDER)} log={win.mission_log.toPlainText().count(chr(10)) + 1}lines")
        print(f"SMOKE OK: {win.windowTitle()} theme applied, size={win.size().width()}x{win.size().height()}")
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
