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


def _maybe_splash(app) -> object | None:
    """DRDO-style loading splash. Skipped offscreen (tests/CI/smoke)."""
    import os

    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        return None
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
        from PySide6.QtWidgets import QSplashScreen

        pix = QPixmap(520, 260)
        pix.fill(QColor("#020617"))
        p = QPainter(pix)
        p.setPen(QColor("#10b981"))
        p.setFont(QFont("monospace", 28, QFont.Bold))
        p.drawText(28, 80, "SIGNIT")
        p.setPen(QColor("#67e8f9"))
        p.setFont(QFont("monospace", 11))
        p.drawText(28, 112, "RF SIGNAL ANALYZER  //  OFFLINE • LOCAL")
        p.setPen(QColor("#64748b"))
        p.setFont(QFont("monospace", 10))
        p.drawText(28, 150, "loading DSP chain … estimators • demod • ML vote • FEC")
        p.drawText(28, 180, "no network  •  local history  •  chain-of-custody hash")
        p.end()
        splash = QSplashScreen(pix, Qt.WindowStaysOnTopHint)
        splash.setObjectName("signitSplash")
        splash.show()
        splash.showMessage("initializing …", Qt.AlignBottom | Qt.AlignHCenter, QColor("#6ee7b7"))
        app.processEvents()
        return splash
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    from app.mainwindow import MainWindow

    parser = argparse.ArgumentParser(prog="SIGNIT")
    parser.add_argument("--smoke", action="store_true", help="open and immediately close (headless check)")
    parser.add_argument("--history-db", default=None, help="override local history DB path (default: platform local)")
    parser.add_argument("--no-splash", action="store_true", help="skip loading splash")
    args = parser.parse_args(argv)

    app = create_app(sys.argv if argv is None else [sys.argv[0], *argv] if argv else sys.argv)
    splash = None if (args.no_splash or args.smoke) else _maybe_splash(app)
    win = MainWindow(history_db=args.history_db)
    win.show()
    if splash is not None:
        try:
            from PySide6.QtCore import QTimer

            splash.finish(win)
        except Exception:
            pass
    if args.smoke:
        # F3 smoke: live cycle — synth reference through the real chain,
        # every tab offscreen. Plus one fallback sanity check.
        from app.demo_store import validate_demo
        from app.mainwindow import SYNTH_MAP
        from app.widgets.results_tabs import TAB_ORDER

        app.processEvents()
        for demo_id in SYNTH_MAP:
            ok = win.open_synthetic_reference(demo_id)
            app.processEvents()
            for index in range(len(TAB_ORDER)):
                win.results_tabs.setCurrentIndex(index)
                app.processEvents()
            errs = validate_demo(win._demo) if win._demo else ["no demo"]
            print(f"SMOKE live={demo_id} ok={ok} valid={errs == []} tabs={len(TAB_ORDER)} mod={win.side_report.mod_label.text()}")
            assert ok and errs == [], f"smoke live {demo_id} failed: {errs}"
        fb = win.open_demo("qpsk")
        print(f"SMOKE fallback=qpsk ok={fb}")
        print(f"SMOKE OK: {win.windowTitle()} theme applied, size={win.size().width()}x{win.size().height()}")
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
