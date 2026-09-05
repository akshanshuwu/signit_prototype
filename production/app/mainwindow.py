"""Ops-console main window (Phase 1).

Layout: header bar (S badge + SIGNIT + nav) on top; horizontal splitter
with left FilePanel / center ResultsTabs / right ReportCard; Mission Log
docked at the bottom. Selecting a sample loads the bundled demo JSON into
all tabs + right report + log (web results-page parity).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.demo_store import DEMO_IDS, load_demo
from app.widgets.file_panel import FilePanel
from app.widgets.mission_log import MissionLog
from app.widgets.report_card import ReportCard
from app.widgets.results_tabs import TAB_ORDER, ResultsTabs

APP_TITLE = "SIGNIT — RF Signal Analyzer"
APP_OBJECT_NAME = "SignitMainWindow"


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(APP_OBJECT_NAME)
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 800)
        self._demo_id: str | None = None

        root = QWidget(self)
        root.setObjectName("rootWidget")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setObjectName("rootLayout")
        root_layout.setContentsMargins(8, 8, 8, 8)

        # Header bar (layout.tsx parity)
        header = QWidget(root)
        header.setObjectName("headerBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 4, 4, 4)
        badge = QLabel("S", header)
        badge.setObjectName("brandBadge")
        badge.setStyleSheet(
            "background: #10b981; color: #020617; font-weight: 900; "
            "font-size: 14px; padding: 2px 8px; border-radius: 4px;"
        )
        title = QLabel("SIGNIT  <span style='color:#64748b;'>RF Signal Analyzer</span>", header)
        title.setObjectName("brandTitle")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #f1f5f9;")
        header_layout.addWidget(badge)
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        self.nav_analyzer_btn = QPushButton("Analyzer", header)
        self.nav_analyzer_btn.setObjectName("navAnalyzerButton")
        self.nav_sample_btn = QPushButton("Sample analysis", header)
        self.nav_sample_btn.setObjectName("navSampleButton")
        self.nav_sample_btn.clicked.connect(lambda: self.open_demo("qpsk"))
        header_layout.addWidget(self.nav_analyzer_btn)
        header_layout.addWidget(self.nav_sample_btn)
        root_layout.addWidget(header)

        # Error banner (invalid id parity with web red box)
        self.error_banner = QLabel("", root)
        self.error_banner.setObjectName("errorBanner")
        self.error_banner.setWordWrap(True)
        self.error_banner.setStyleSheet(
            "color: #fecaca; background: #450a0a; border: 1px solid #7f1d1d; padding: 6px; font-size: 12px;"
        )
        self.error_banner.hide()
        root_layout.addWidget(self.error_banner)

        # Main splitter: left / center / right
        splitter = QSplitter(Qt.Horizontal, root)
        splitter.setObjectName("mainSplitter")

        self.file_panel = FilePanel(splitter)
        self.file_panel.sample_selected.connect(self.open_demo)

        self.results_tabs = ResultsTabs(splitter)

        self.side_report = ReportCard(splitter)
        self.side_report.setObjectName("sideReportCard")

        splitter.addWidget(self.file_panel)
        splitter.addWidget(self.results_tabs)
        splitter.addWidget(self.side_report)
        splitter.setSizes([260, 700, 320])
        root_layout.addWidget(splitter, 1)

        # Bottom: processing log (always visible, like web)
        log_title = QLabel("Processing log", root)
        log_title.setObjectName("logTitle")
        log_title.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: bold;")
        root_layout.addWidget(log_title)
        self.mission_log = MissionLog(root)
        self.mission_log.setMaximumHeight(140)
        root_layout.addWidget(self.mission_log)

        self.setStyleSheet("QMainWindow { background: #020617; } QLabel { color: #e2e8f0; }")

        # Default view mirrors web CTA: sample analysis (qpsk).
        self.open_demo("qpsk")

    @property
    def demo_id(self) -> str | None:
        return self._demo_id

    def open_demo(self, demo_id: str) -> bool:
        """Load a demo into every panel. Returns False + red banner on unknown id."""
        try:
            demo = load_demo(demo_id)
        except ValueError as exc:
            self.error_banner.setText(str(exc))
            self.error_banner.show()
            return False
        except FileNotFoundError:
            self.error_banner.setText(f"demo {demo_id} not found")
            self.error_banner.show()
            return False
        self.error_banner.hide()
        self._demo_id = demo_id
        self.setWindowTitle(f"{APP_TITLE} · {demo_id.upper()}")
        self.results_tabs.set_demo(demo)
        self.side_report.set_data(demo)
        self.mission_log.set_lines(demo.get("log", []))
        return True

    def available_demos(self) -> tuple:
        return DEMO_IDS
