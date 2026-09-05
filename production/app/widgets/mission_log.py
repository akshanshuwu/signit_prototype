"""Mission Log — mono terminal panel (web MissionLog parity)."""
from PySide6.QtWidgets import QPlainTextEdit


class MissionLog(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("missionLog")
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)
        self.setStyleSheet(
            "QPlainTextEdit#missionLog { background: rgba(0,0,0,0.4); color: #6ee7b7; "
            "font-family: monospace; font-size: 12px; border: 1px solid #1e293b; }"
        )

    def set_lines(self, lines: list[str]) -> None:
        if not lines:
            self.setPlainText("$ no logs")
            return
        self.setPlainText("\n".join(f"$ {line}" for line in lines))
