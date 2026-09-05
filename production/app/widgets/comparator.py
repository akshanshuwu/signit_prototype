"""Comparator — .IQ vs .wav SNR cards + degradation note (web parity)."""
from PySide6.QtWidgets import QGridLayout, QLabel, QProgressBar, QVBoxLayout, QWidget


class Comparator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("comparator")

        layout = QVBoxLayout(self)
        cards = QGridLayout()
        cards.setObjectName("comparatorCards")

        self.iq_value = QLabel("—", self)
        self.iq_value.setObjectName("iqSnrValue")
        self.iq_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #6ee7b7;")
        self.iq_bar = QProgressBar(self)
        self.iq_bar.setObjectName("iqSnrBar")
        self.iq_bar.setRange(0, 100)
        self.iq_bar.setTextVisible(False)

        self.wav_value = QLabel("—", self)
        self.wav_value.setObjectName("wavSnrValue")
        self.wav_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #e2e8f0;")
        self.wav_bar = QProgressBar(self)
        self.wav_bar.setObjectName("wavSnrBar")
        self.wav_bar.setRange(0, 100)
        self.wav_bar.setTextVisible(False)

        iq_title = QLabel(".IQ (complex, full phase)", self)
        iq_title.setStyleSheet("color: #94a3b8; font-size: 11px;")
        wav_title = QLabel(".wav (real, BW-limited)", self)
        wav_title.setStyleSheet("color: #94a3b8; font-size: 11px;")

        cards.addWidget(iq_title, 0, 0)
        cards.addWidget(self.iq_value, 1, 0)
        cards.addWidget(self.iq_bar, 2, 0)
        cards.addWidget(wav_title, 0, 1)
        cards.addWidget(self.wav_value, 1, 1)
        cards.addWidget(self.wav_bar, 2, 1)

        self.note = QLabel("", self)
        self.note.setObjectName("comparatorNote")
        self.note.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.note.setWordWrap(True)

        layout.addLayout(cards)
        layout.addWidget(self.note)
        layout.addStretch(1)

    def set_data(self, iq_snr: float, wav_snr: float, note: str) -> None:
        maximum = max(iq_snr, wav_snr, 1)
        self.iq_value.setText(f"{iq_snr:.1f} dB")
        self.wav_value.setText(f"{wav_snr:.1f} dB")
        self.iq_bar.setValue(round(iq_snr / maximum * 100))
        self.wav_bar.setValue(round(wav_snr / maximum * 100))
        self.note.setText(f"Degradation: {iq_snr - wav_snr:.1f} dB — {note}")
