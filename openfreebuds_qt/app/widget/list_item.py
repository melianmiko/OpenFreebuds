from PyQt6.QtWidgets import QWidget

from openfreebuds_qt.designer.list_item import Ui_ListItem


class OfbQListItem(Ui_ListItem, QWidget):
    def __init__(self, parent: QWidget, text: str = ""):
        super().__init__(parent)

        self.setupUi(self)
        self.label.setText(text)

    def set_active(self, value: bool):
        self.label.setProperty("itemActive", "true" if value else "false")
        style = self.style()
        style.unpolish(self.label)
        style.polish(self.label)
