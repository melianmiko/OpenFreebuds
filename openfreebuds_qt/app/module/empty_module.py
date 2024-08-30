from PyQt6.QtWidgets import QWidget, QLabel

from openfreebuds_qt.app.module.common import OfbQtCommonModule


class OfbEmptyModule(OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        QLabel("Not implemented yet", self)
