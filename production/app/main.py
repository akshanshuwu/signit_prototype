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
    """Loading splash. Skipped offscreen (tests/CI/smoke)."""
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
        p.drawText(28, 112, "RF SIGNAL ANALYZER")
        p.setPen(QColor("#64748b"))
        p.setFont(QFont("monospace", 10))
        p.drawText(28, 150, "loading … estimators • demod • ML vote • FEC")
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

    # Qt must only see the program name: app flags (--smoke/--history-db)
    # are argparse-owned, unknown args make QApplication warn/fail.
    app = create_app([sys.argv[0]])
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
        # Smoke: temp .iq files through the REAL ingest + chain, every
        # tab offscreen. No synth buttons, no bundled demos — file ingest
        # is the only path.
        import os
        import tempfile

        from app.demo_store import validate_demo
        from app.widgets.results_tabs import TAB_ORDER
        from engine.ingest import ingest_file
        from ml.synth import FS, synth

        app.processEvents()
        tmp = tempfile.mkdtemp(prefix="signit_smoke_")
        for mod in ("BPSK", "QPSK", "16QAM", "2FSK"):
            path = os.path.join(tmp, f"smoke_{mod.lower()}.iq")
            synth(mod, 15.0, 7).tofile(path)
            win._on_ingested(ingest_file(path, fs=int(FS)))
            app.processEvents()
            for index in range(len(TAB_ORDER)):
                win.results_tabs.setCurrentIndex(index)
                app.processEvents()
            errs = validate_demo(win._demo) if win._demo else ["no demo"]
            print(f"SMOKE live={mod.lower()} valid={errs == []} tabs={len(TAB_ORDER)} mod={win.side_report.mod_label.text()}")
            assert win._source == "live" and errs == [], f"smoke live {mod} failed: {errs}"
        print(f"SMOKE OK: {win.windowTitle()} theme applied, size={win.size().width()}x{win.size().height()}")
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
