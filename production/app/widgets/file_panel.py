"""File panel — left dock: drop/select file, params, sample cards.

Web UploadBox parity: accepts .iq/.wav/.bin; same validation messages;
Phase 1 validates only (real ingest lands in Phase 2) and points at samples.
"""
import os
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.demo_store import DEMO_IDS, SAMPLE_META

MAX_MB = 15
_EXT_RE = re.compile(r"\.(iq|wav|bin)$", re.IGNORECASE)


def validate_file(name: str, size_bytes: int) -> str:
    """Mirror web UploadBox messages exactly."""
    if not _EXT_RE.search(name):
        return f"{name} isn't supported — please use .iq, .wav or .bin files."
    if size_bytes > MAX_MB * 1024 * 1024:
        return (
            f"{name} is {size_bytes / 1048576:.1f} MB — files up to {MAX_MB} MB "
            f"are accepted. Try a sample capture below."
        )
    return f"{name} passed validation. Open a sample capture below to explore the full analysis."


class FilePanel(QWidget):
    sample_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("filePanel")
        layout = QVBoxLayout(self)
        layout.setObjectName("filePanelLayout")

        # Drop / browse box
        drop_group = QGroupBox("Capture", self)
        drop_group.setObjectName("dropGroup")
        drop_layout = QVBoxLayout(drop_group)
        self.drop_label = QLabel("Drop an .iq, .wav or .bin file here, or click Browse.\nUp to 15 MB.", drop_group)
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

        # Sample captures
        samples_group = QGroupBox("Sample captures", self)
        samples_group.setObjectName("samplesGroup")
        samples_layout = QVBoxLayout(samples_group)
        self.sample_buttons: dict[str, QPushButton] = {}
        for demo_id in DEMO_IDS:
            mod, desc = SAMPLE_META[demo_id]
            btn = QPushButton(f"{mod}\n{desc}", samples_group)
            btn.setObjectName(f"sampleButton_{demo_id}")
            btn.clicked.connect(lambda _=False, d=demo_id: self.sample_selected.emit(d))
            samples_layout.addWidget(btn)
            self.sample_buttons[demo_id] = btn
        layout.addWidget(samples_group)
        layout.addStretch(1)

    def show_message(self, text: str) -> None:
        self.validation_msg.setText(text)
        self.validation_msg.show()

    def check_path(self, path: str) -> str:
        """Validate a real file path; shows message; returns message text."""
        name = os.path.basename(path)
        try:
            size = os.path.getsize(path)
        except OSError:
            msg = f"{name} could not be read."
            self.show_message(msg)
            return msg
        msg = validate_file(name, size)
        self.show_message(msg)
        return msg

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
