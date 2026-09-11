"""File panel — left dock: drop/select file, params, history.

Accepts .iq/.wav/.bin for live local analysis. File ingest is the only
analysis path — no sample buttons, no bundled demos.
"""
import os
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

MAX_MB = 2048
MAX_LABEL = "2 GB"
_EXT_RE = re.compile(r"\.(iq|wav|bin)$", re.IGNORECASE)


def validate_file(name: str, size_bytes: int) -> str:
    """Mirror web UploadBox messages (cap raised to 2 GB for desktop memmap ingest)."""
    if not _EXT_RE.search(name):
        return f"{name} isn't supported — please use .iq, .wav or .bin files."
    if size_bytes > MAX_MB * 1024 * 1024:
        return (
            f"{name} is {size_bytes / 1048576:.1f} MB — files up to {MAX_LABEL} "
            f"are accepted."
        )
    return f"{name} passed validation. Ingesting for live analysis…"


class FilePanel(QWidget):
    file_ingested = Signal(object)  # emits engine.ingest.IngestResult
    reanalyze_requested = Signal(dict)  # {t0_s|None, t1_s|None, snr_db|None, freq_offset_hz}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("filePanel")
        layout = QVBoxLayout(self)
        layout.setObjectName("filePanelLayout")

        # Drop / browse box
        drop_group = QGroupBox("Capture", self)
        drop_group.setObjectName("dropGroup")
        drop_layout = QVBoxLayout(drop_group)
        self.drop_label = QLabel("▼ DROP any .iq / .wav / .bin here, or Browse ▼\nUp to 2 GB (memmap).", drop_group)
        self.drop_label.setObjectName("dropLabel")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("color: #94a3b8; padding: 16px;")
        self.browse_btn = QPushButton("Browse…", drop_group)
        self.browse_btn.setObjectName("browseButton")
        self.browse_btn.clicked.connect(self._browse)
        drop_layout.addWidget(self.drop_label)
        drop_layout.addWidget(self.browse_btn)
        drop_group.setAcceptDrops(True)
        drop_group.dragEnterEvent = self._drag_enter
        drop_group.dropEvent = self._drop
        layout.addWidget(drop_group)

        self.validation_msg = QLabel("", self)
        self.validation_msg.setObjectName("validationMsg")
        self.validation_msg.setWordWrap(True)
        self.validation_msg.setStyleSheet(
            "color: #fcd34d; background: rgba(120,53,15,0.4); "
            "border: 1px solid #92400e; padding: 6px; font-size: 11px;"
        )
        self.validation_msg.hide()
        layout.addWidget(self.validation_msg)

        # Params (display-only in Phase 1; wired to engine in Phase 2)
        params_group = QGroupBox("Parameters", self)
        params_group.setObjectName("paramsGroup")
        form = QFormLayout(params_group)
        self.fs_combo = QComboBox(params_group)
        self.fs_combo.setObjectName("fsCombo")
        self.fs_combo.addItems(["48000", "96000", "192000", "1000000"])
        self.fc_combo = QComboBox(params_group)
        self.fc_combo.setObjectName("fcCombo")
        self.fc_combo.addItems(["0 (baseband)", "100000", "1000000"])
        self.dtype_combo = QComboBox(params_group)
        self.dtype_combo.setObjectName("dtypeCombo")
        self.dtype_combo.addItems(["complex64 (I/Q interleaved float32)", "int16 (I/Q interleaved)", "complex128"])
        form.addRow("fs (Hz):", self.fs_combo)
        form.addRow("fc (Hz):", self.fc_combo)
        form.addRow("dtype:", self.dtype_combo)
        layout.addWidget(params_group)

        # Re-analysis: ROI slice + impairment probes on the ingested capture.
        re_group = QGroupBox("Re-analysis (ROI + impairments)", self)
        re_group.setObjectName("reanalysisGroup")
        re_form = QFormLayout(re_group)
        self.roi_t0 = QDoubleSpinBox(re_group)
        self.roi_t0.setObjectName("roiStartSpin")
        self.roi_t0.setRange(0.0, 3600.0)
        self.roi_t0.setDecimals(2)
        self.roi_t0.setSuffix(" s")
        self.roi_t0.setSpecialValueText("start")
        self.roi_t1 = QDoubleSpinBox(re_group)
        self.roi_t1.setObjectName("roiEndSpin")
        self.roi_t1.setRange(0.0, 3600.0)
        self.roi_t1.setDecimals(2)
        self.roi_t1.setSuffix(" s")
        self.roi_t1.setSpecialValueText("end")
        self.impair_snr = QComboBox(re_group)
        self.impair_snr.setObjectName("impairSnrCombo")
        self.impair_snr.addItems(["off", "20 dB", "12 dB", "8 dB", "5 dB"])
        self.impair_fo = QSpinBox(re_group)
        self.impair_fo.setObjectName("impairFoSpin")
        self.impair_fo.setRange(-5000, 5000)
        self.impair_fo.setSuffix(" Hz")
        self.reanalyze_btn = QPushButton("Re-analyze", re_group)
        self.reanalyze_btn.setObjectName("reanalyzeButton")
        self.reanalyze_btn.clicked.connect(self._request_reanalyze)
        re_form.addRow("slice start:", self.roi_t0)
        re_form.addRow("slice end:", self.roi_t1)
        re_form.addRow("+AWGN:", self.impair_snr)
        re_form.addRow("+freq offset:", self.impair_fo)
        re_form.addRow(self.reanalyze_btn)
        layout.addWidget(re_group)

        # History — list + refresh, no network.
        hist_group = QGroupBox("History", self)
        hist_group.setObjectName("historyGroup")
        hist_layout = QVBoxLayout(hist_group)
        self.history_list = QListWidget(hist_group)
        self.history_list.setObjectName("historyList")
        self.history_list.setMaximumHeight(140)
        self.history_list.setStyleSheet(
            "QListWidget#historyList { background: rgba(0,0,0,0.4); color: #6ee7b7; "
            "font-family: monospace; font-size: 11px; border: 1px solid #1e293b; }"
        )
        self.history_detail = QLabel("no runs yet — analyze a capture", hist_group)
        self.history_detail.setObjectName("historyDetail")
        self.history_detail.setWordWrap(True)
        self.history_detail.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.history_refresh_btn = QPushButton("Refresh", hist_group)
        self.history_refresh_btn.setObjectName("historyRefreshButton")
        self.history_refresh_btn.clicked.connect(lambda: self.refresh_history())
        self.history_list.itemClicked.connect(self._show_history_detail)
        hist_layout.addWidget(self.history_list)
        hist_layout.addWidget(self.history_detail)
        hist_layout.addWidget(self.history_refresh_btn)
        layout.addWidget(hist_group)
        self._history_db: str | None = None
        self._history_rows: list = []
        layout.addStretch(1)

    def refresh_history(self, db_path: str | None = None) -> int:
        """Reload the local history list. Returns row count (0 when empty/missing)."""
        from engine.history import list_runs

        if db_path is not None:
            self._history_db = db_path
        path = self._history_db
        if not path:
            from engine.history import default_db_path

            path = default_db_path()
            self._history_db = path
        try:
            rows = list_runs(path, limit=100)
        except Exception:
            rows = []
        self._history_rows = rows
        self.history_list.clear()
        for r in rows:
            self.history_list.addItem(
                f"#{r['id']} {r['modulation']} {r['confidence']:.2f} · {r['filename']} · {r['ts']}"
            )
        if rows:
            self.history_detail.setText(f"{len(rows)} run(s) — click for details")
        else:
            self.history_detail.setText("no runs yet — analyze a capture")
        return len(rows)

    def _show_history_detail(self, item) -> None:
        idx = self.history_list.row(item)
        if 0 <= idx < len(self._history_rows):
            r = self._history_rows[idx]
            self.history_detail.setText(
                f"#{r['id']} {r['filename']} · {r['modulation']} @ {r['confidence']:.2f} · "
                f"SNR {r['snr']:.1f}dB BW {r['bw']:.0f}Hz sr {r['symbol_rate']} · "
                f"sha {str(r['sha256'])[:12]}… · {r['source']}"
            )

    def show_message(self, text: str) -> None:
        self.validation_msg.setText(text)
        self.validation_msg.show()

    def _request_reanalyze(self) -> None:
        """Emit the ROI/impairment spec; 0.0 spin = unbounded slice edge."""
        snr_txt = self.impair_snr.currentText()
        self.reanalyze_requested.emit({
            "t0_s": None if self.roi_t0.value() <= 0.0 else float(self.roi_t0.value()),
            "t1_s": None if self.roi_t1.value() <= 0.0 else float(self.roi_t1.value()),
            "snr_db": None if snr_txt == "off" else float(snr_txt.split()[0]),
            "freq_offset_hz": float(self.impair_fo.value()),
        })

    def check_path(self, path: str) -> str:
        """Validate + ingest a real file path; shows message; returns message text.

        Phase 2: runs the real ingest engine (memmap count + streaming hash +
        bounded preview). Emits file_ingested on success.
        """
        from engine.ingest import IngestError, ingest_file

        name = os.path.basename(path)
        try:
            size = os.path.getsize(path)
        except OSError:
            msg = f"{name} could not be read."
            self.show_message(msg)
            return msg
        msg = validate_file(name, size)
        if "passed validation" not in msg:
            self.show_message(msg)
            return msg
        try:
            result = ingest_file(
                path,
                fs=int(self.fs_combo.currentText()),
                fc=float(str(self.fc_combo.currentText()).split()[0]),
                dtype_label=self.dtype_combo.currentText(),
            )
        except IngestError as exc:
            self.show_message(str(exc))
            return str(exc)
        done = (
            f"{name}: {result.n_samples} samples @ {result.fs} Hz "
            f"({result.duration_s:.2f} s), sha256 {result.sha256[:12]}…"
        )
        self.show_message(done)
        self.file_ingested.emit(result)
        return done

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open capture", "", "Captures (*.iq *.wav *.bin);;All (*)"
        )
        if path:
            self.check_path(path)

    def _drag_enter(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            self.check_path(urls[0].toLocalFile())
