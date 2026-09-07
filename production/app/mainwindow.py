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

import os

import numpy as np

from app.demo_store import DEMO_IDS, load_demo
from app.widgets.file_panel import FilePanel
from app.widgets.mission_log import MissionLog
from app.widgets.report_card import ReportCard
from app.widgets.results_tabs import TAB_ORDER, ResultsTabs

APP_TITLE = "SIGNIT — RF Signal Analyzer"
APP_OBJECT_NAME = "SignitMainWindow"

STAGES = ("ingest", "est", "demod", "vote", "fec")


def tick_line(done: list[str], failed: list[str] | None = None) -> str:
    """One-click Auto-Chain summary: per-stage ✓/✗ ticks for the mission log."""
    failed = set(failed or [])
    return "auto-chain: " + " → ".join(
        f"{s} {'✗' if s in failed else '✓'}" for s in STAGES if s in done or s in failed
    ) or "auto-chain: no stages ran"


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(APP_OBJECT_NAME)
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 800)
        self._demo_id: str | None = None
        self._demo: dict | None = None  # last demo dict shown (for PDF export)
        self._ingest = None  # last IngestResult (for ROI/impairment re-analysis)

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
        self.pdf_btn = QPushButton("Export PDF", header)
        self.pdf_btn.setObjectName("exportPdfButton")
        self.pdf_btn.clicked.connect(self._export_pdf)
        header_layout.addWidget(self.nav_analyzer_btn)
        header_layout.addWidget(self.nav_sample_btn)
        header_layout.addWidget(self.pdf_btn)
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
        self.file_panel.file_ingested.connect(self._on_ingested)
        self.file_panel.reanalyze_requested.connect(
            lambda spec: self.reanalyze(spec.get("t0_s"), spec.get("t1_s"),
                                        spec.get("snr_db"), spec.get("freq_offset_hz", 0.0))
        )

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
        self._demo = demo
        self._ingest = None
        self.setWindowTitle(f"{APP_TITLE} · {demo_id.upper()}")
        self.results_tabs.set_demo(demo)
        self.side_report.set_data(demo)
        self.mission_log.set_lines(
            list(demo.get("log", [])) + [tick_line(["ingest", "est", "demod", "vote", "fec"])]
        )
        return True

    def available_demos(self) -> tuple:
        return DEMO_IDS

    def export_pdf_to(self, path: str) -> str:
        """Write the Intel PDF for the currently shown demo. Returns path."""
        if self._demo is None:
            raise ValueError("nothing to export — open a sample or ingest a file first")
        from app.intel_pdf import write_intel_pdf

        log = [line[2:] if line.startswith("$ ") else line for line in self.mission_log.toPlainText().splitlines()]
        return write_intel_pdf(self._demo, path, log)

    def _export_pdf(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(self, "Export Intel PDF", "SIGNIT_report.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            self.export_pdf_to(path)
            current = self.mission_log.toPlainText()
            extra = f"$ intel pdf written: {path}"
            self.mission_log.setPlainText(current + ("\n" if current else "") + extra)
            self.error_banner.hide()
        except Exception as exc:
            self.error_banner.setText(f"pdf export failed: {exc}")
            self.error_banner.show()

    def _on_ingested(self, result) -> None:
        """Phase 6: estimators + demod + ML vote + FEC assessment; report shows ensemble winner."""
        from engine.ingest import log_lines

        self._ingest = result
        self._run_chain(result.preview, result.fs, result.fc,
                        os.path.basename(result.path), log_lines(result),
                        kind=result.kind, sha256=result.sha256,
                        n_samples=result.n_samples, path=result.path)

    def _run_chain(self, preview, fs: int, fc: float, title_label: str, base_lines: list,
                   kind: str = "iq", sha256: str = "", n_samples: int | None = None,
                   path: str | None = None) -> None:
        """Run estimators → demod → vote → fec on any preview; update all panels."""
        from engine.demod import demod_log_lines, demodulate_preview
        from engine.estimators import analyze_preview, estimator_log_lines, to_demo_dict

        # Minimal stand-in carrying path/fs/fc/kind for to_demo_dict.
        from engine.ingest import IngestResult

        preview = np.asarray(preview, dtype=np.complex64).ravel()
        ingest_view = IngestResult(path=path or title_label, kind=kind,
                                   n_samples=len(preview) if n_samples is None else n_samples,
                                   fs=int(fs), fc=float(fc),
                                   dtype_label="chain-preview", sha256=sha256,
                                   preview=preview.astype(np.complex64))
        done, failed = ["ingest"], []
        try:
            est = analyze_preview(preview, fs, fc)
            done.append("est")
        except Exception as exc:  # never leave the console blank on estimator failure
            self.error_banner.setText(f"estimators failed: {exc}")
            self.error_banner.show()
            self.mission_log.set_lines(base_lines + [tick_line(done, failed + ["est"])])
            return
        try:
            demod = demodulate_preview(preview, fs)
            demod_lines = demod_log_lines(demod)
            done.append("demod")
            if demod.modulation == "UNKNOWN":
                failed.append("demod")
        except Exception as exc:  # demod failure falls back to estimator-only view
            demod = None
            demod_lines = [f"demod failed: {exc} — showing estimator-only view"]
            failed.append("demod")
        try:
            from ml.ensemble import run_ml_vote

            _cum, vote, _cnn, ml_lines = run_ml_vote(preview, fs, demod)
            done.append("vote")
            if vote.winner == "UNKNOWN":
                failed.append("vote")
        except Exception as exc:  # ML failure keeps the demod view
            vote, ml_lines = None, [f"ml vote failed: {exc} — showing demod view"]
            failed.append("vote")
        try:
            from engine.fec import assess_bits, fec_log_lines

            fec = assess_bits(demod.bits) if demod is not None and len(demod.bits) >= 64 else None
            fec_lines = fec_log_lines(fec) if fec is not None else ["fec: no bits — assessment skipped"]
            done.append("fec")
            if fec is None or getattr(fec, "status", "NONE") == "NONE":
                failed.append("fec")
        except Exception as exc:  # FEC failure keeps the ML view
            fec, fec_lines = None, [f"fec failed: {exc} — showing ML view"]
            failed.append("fec")
        self.error_banner.hide()
        demo = to_demo_dict(est, ingest_view, demod=demod, vote=vote, fec=fec)
        self._demo_id = None
        self._demo = demo
        self.setWindowTitle(f"{APP_TITLE} · {title_label}")
        self.results_tabs.set_demo(demo)
        self.side_report.set_data(demo)
        self.mission_log.set_lines(
            list(base_lines) + estimator_log_lines(est) + demod_lines + ml_lines + fec_lines
            + [tick_line(done, failed)]
        )

    def reanalyze(self, t0_s: float | None = None, t1_s: float | None = None,
                  snr_db: float | None = None, freq_offset_hz: float = 0.0) -> bool:
        """ROI/impairment re-analysis on the last ingested capture.

        Slices [t0_s, t1_s) when given, then applies AWGN / freq-offset
        probes. Re-runs the standard chain so views stay comparable.
        Returns False + banner when there is nothing to re-analyze.
        """
        if self._ingest is None:
            self.error_banner.setText("nothing to re-analyze — ingest a file first")
            self.error_banner.show()
            return False
        from engine.reanalyze import add_awgn, add_freq_offset, slice_duration_s, slice_preview

        res = self._ingest
        dur = slice_duration_s(res.preview, res.fs)
        a = 0.0 if t0_s is None else float(t0_s)
        b = dur if t1_s is None else float(t1_s)
        try:
            work = slice_preview(res.preview, res.fs, a, b)
        except ValueError as exc:
            self.error_banner.setText(str(exc))
            self.error_banner.show()
            return False
        probes = []
        if snr_db is not None:
            work = add_awgn(work, float(snr_db))
            probes.append(f"+awgn@{snr_db:.0f}dB")
        if freq_offset_hz:
            work = add_freq_offset(work, res.fs, float(freq_offset_hz))
            probes.append(f"{freq_offset_hz:+.0f}Hz")
        label = f"{os.path.basename(res.path)}[{a:.1f}-{b:.1f}s{''.join(probes)}]"
        self._run_chain(work, res.fs, res.fc, label,
                        [f"re-analysis of {os.path.basename(res.path)}: slice [{a:.2f}, {b:.2f})s"
                         + (" " + " ".join(probes) if probes else " (clean slice)")],
                        kind=res.kind, sha256=res.sha256, path=res.path)
        return True
