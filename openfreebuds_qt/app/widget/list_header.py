from PyQt6.QtWidgets import QLabel, QWidget


class OfbQListHeader(QLabel):
    def __init__(self, parent: QWidget, text: str = ""):
        super().__init__(parent)
        self.setStyleSheet("font-weight: bold;"
                           "font-size: 14px;"
                           "padding: 8px 12px;"
                           "color: palette(link)")
        self.setText(text)

    def setText(self, a0: str):
        super().setText(a0.upper())
