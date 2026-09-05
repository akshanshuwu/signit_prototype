"""ResultsTabs — center panel: 6 tabs in web order (web parity).

Order: Report | Spectrum | Waterfall | Constellation | Compare | Bits.
"""
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from app.widgets.bits_view import BitsView
from app.widgets.comparator import Comparator
from app.widgets.plots import (
    ConstellationPlotWidget,
    SpectrumPlotWidget,
    WaterfallPlotWidget,
)
from app.widgets.report_card import ReportCard

TAB_ORDER = ("report", "spectrum", "waterfall", "constellation", "compare", "bits")
TAB_LABELS = {
    "report": "Report",
    "spectrum": "Spectrum",
    "waterfall": "Waterfall",
    "constellation": "Constellation",
    "compare": "Compare",
    "bits": "Bits",
}


class ResultsTabs(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultsTabs")

        self.report = ReportCard(self)
        self.spectrum = SpectrumPlotWidget(self)
        self.waterfall = WaterfallPlotWidget(self)
        self.constellation = ConstellationPlotWidget(self)
        self.comparator = Comparator(self)
        self.bits = BitsView(self)

        self._pages: dict[str, QWidget] = {
            "report": self.report,
            "spectrum": self._wrap("Spectrum (PSD)", self.spectrum),
            "waterfall": self._wrap("Waterfall (time-frequency)", self.waterfall),
            "constellation": self._wrap("Constellation (I/Q)", self.constellation),
            "compare": self._wrap(".IQ vs .wav", self.comparator),
            "bits": self._wrap("Bits + correlation", self.bits),
        }
        for tab_id in TAB_ORDER:
            self.addTab(self._pages[tab_id], TAB_LABELS[tab_id])
        self.setCurrentIndex(0)

    def _wrap(self, title: str, widget: QWidget) -> QWidget:
        page = QWidget(self)
        page.setObjectName(f"tabPage_{title}")
        layout = QVBoxLayout(page)
        header = QLabel(title, page)
        header.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: bold;")
        layout.addWidget(header)
        layout.addWidget(widget, 1)
        return page

    def set_demo(self, demo: dict) -> None:
        """Populate all tabs from one demo dict (no refetch on tab switch)."""
        self.report.set_data(demo)
        self.spectrum.set_data(demo["psd"]["freqs"], demo["psd"]["mags_db"])
        spec = demo["spectrogram"]
        self.waterfall.set_data(spec["times"], spec["freqs"], spec["z_db"])
        self.constellation.set_data(demo["constellation"]["i"], demo["constellation"]["q"])
        comp = demo["comparator"]
        self.comparator.set_data(comp["iq_snr"], comp["wav_snr"], comp["note"])
        bp = demo["bits_preview"]
        self.bits.set_data(bp["hex"], bp["ascii"], bp["corr_peak"])

    def tab_id(self, index: int) -> str:
        return TAB_ORDER[index]
