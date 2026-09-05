"""ReportCard — modulation + confidence + estimates + votes (web parity)."""
from PySide6.QtWidgets import QGridLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.demo_store import format_khz


class ReportCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("reportCard")

        layout = QVBoxLayout(self)
        layout.setObjectName("reportLayout")

        self.mod_label = QLabel("—", self)
        self.mod_label.setObjectName("modLabel")
        self.mod_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f1f5f9;")

        self.conf_label = QLabel("—", self)
        self.conf_label.setObjectName("confLabel")
        self.conf_label.setStyleSheet("font-size: 13px; color: #67e8f9;")

        self.conf_bar = QProgressBar(self)
        self.conf_bar.setObjectName("confBar")
        self.conf_bar.setRange(0, 100)
        self.conf_bar.setTextVisible(False)
        self.conf_bar.setStyleSheet(
            "QProgressBar#confBar { background: #1e293b; border-radius: 4px; height: 8px; }"
            "QProgressBar#confBar::chunk { background: #10b981; border-radius: 4px; }"
        )

        self.grid = QGridLayout()
        self.grid.setObjectName("reportGrid")
        self._cells: dict[str, QLabel] = {}
        for row, key in enumerate(
            ["fs", "symbol", "bw", "snr", "cnn", "cumulants"]
        ):
            title = QLabel(self._titles()[key], self)
            title.setStyleSheet("color: #64748b; font-size: 11px;")
            value = QLabel("—", self)
            value.setObjectName(f"reportValue_{key}")
            value.setStyleSheet("color: #e2e8f0; font-size: 12px; font-weight: bold;")
            self.grid.addWidget(title, row, 0)
            self.grid.addWidget(value, row, 1)
            self._cells[key] = value

        self.footer = QLabel("", self)
        self.footer.setObjectName("reportFooter")
        self.footer.setStyleSheet("color: #64748b; font-size: 11px;")
        self.footer.setWordWrap(True)

        layout.addWidget(self.mod_label)
        layout.addWidget(self.conf_label)
        layout.addWidget(self.conf_bar)
        layout.addLayout(self.grid)
        layout.addWidget(self.footer)
        layout.addStretch(1)

    @staticmethod
    def _titles() -> dict[str, str]:
        return {
            "fs": "Sampling freq (est)",
            "symbol": "Symbol rate (est)",
            "bw": "Bandwidth (est)",
            "snr": "SNR (est)",
            "cnn": "CNN vote",
            "cumulants": "Cumulants vote",
        }

    def set_data(self, demo: dict) -> None:
        p = demo["predictions"]
        pct = round(p["confidence"] * 100)
        self.mod_label.setText(p["modulation"])
        self.conf_label.setText(f"{pct}% confidence")
        self.conf_bar.setValue(pct)
        self._cells["fs"].setText(f"{p['fs_est']} Hz")
        self._cells["symbol"].setText(f"{p['symbol_rate_est']} sym/s")
        self._cells["bw"].setText(format_khz(p["bw_est"]))
        self._cells["snr"].setText(f"{p['snr_est']:.1f} dB")
        self._cells["cnn"].setText(f"{p['votes']['CNN'] * 100:.0f}% {p['modulation']}")
        self._cells["cumulants"].setText(str(p["votes"]["cumulants"]))
        m = demo["meta"]
        self.footer.setText(
            f"File: {m['file']} · fs {m['fs']} Hz · {m['symbol_rate']} sym/s · SNR {m['snr_db']} dB"
        )
