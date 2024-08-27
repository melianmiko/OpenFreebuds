from PyQt6.QtWidgets import QWidget, QLabel

from openfreebuds_qt.app.module.common import OfbQtCommonModule


class OfbEmptyModule(OfbQtCommonModule):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        QLabel("Not implemented yet", self)
