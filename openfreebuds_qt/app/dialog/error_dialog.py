from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from openfreebuds_qt.utils.async_dialog import OfbQtAsyncDialog
from openfreebuds_qt.designer.dialog_error import Ui_OfbQtErrorDialog


class OfbQtErrorDialog(Ui_OfbQtErrorDialog, OfbQtAsyncDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setupUi(self)

    async def get_user_response(self, info: str = ""):
        self.info_box.setPlainText(info)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        await super().get_user_response()
