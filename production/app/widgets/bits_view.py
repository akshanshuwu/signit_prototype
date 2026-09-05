"""BitsView — hex + ascii preview + sync correlation (web parity)."""
from PySide6.QtWidgets import QGridLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from app.widgets.plots import CorrPeakWidget


class BitsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("bitsView")
        layout = QVBoxLayout(self)

        grid = QGridLayout()
        self.hex_view = QPlainTextEdit(self)
        self.hex_view.setObjectName("hexView")
        self.hex_view.setReadOnly(True)
        self.ascii_view = QPlainTextEdit(self)
        self.ascii_view.setObjectName("asciiView")
        self.ascii_view.setReadOnly(True)
        for view in (self.hex_view, self.ascii_view):
            view.setMaximumBlockCount(100)
            view.setStyleSheet(
                "QPlainTextEdit { background: rgba(0,0,0,0.4); color: #6ee7b7; "
                "font-family: monospace; font-size: 12px; }"
            )
        hex_title = QLabel("Hex (first 32 bytes)", self)
        ascii_title = QLabel("ASCII preview", self)
        for title in (hex_title, ascii_title):
            title.setStyleSheet("color: #64748b; font-size: 11px;")
        grid.addWidget(hex_title, 0, 0)
        grid.addWidget(ascii_title, 0, 1)
        grid.addWidget(self.hex_view, 1, 0)
        grid.addWidget(self.ascii_view, 1, 1)

        self.peak_label = QLabel("", self)
        self.peak_label.setObjectName("corrPeakLabel")
        self.peak_label.setStyleSheet("color: #64748b; font-size: 11px;")
        self.corr_plot = CorrPeakWidget(self)

        layout.addLayout(grid)
        layout.addWidget(self.peak_label)
        layout.addWidget(self.corr_plot, 1)

    def set_data(self, hex_text: str, ascii_text: str, corr_peak: dict) -> None:
        self.hex_view.setPlainText(hex_text)
        self.ascii_view.setPlainText(ascii_text)
        self.peak_label.setText(
            f"Sync correlation peak: lag {corr_peak['lag']}, value {corr_peak['value']:.2f}"
        )
        self.corr_plot.set_data(corr_peak["lags"], corr_peak["vals"], corr_peak["lag"])
