import sys
from PyQt6.QtWidgets import QWidget

from openfreebuds.driver import DEVICE_TO_DRIVER_MAP
from openfreebuds_qt.constants import WIN32_BODY_STYLE
from openfreebuds_qt.utils.async_dialog import OfbQtAsyncDialog
from openfreebuds_qt.designer.dialog_manual_connect import Ui_OfbQtManualConnectDialog


class OfbQtManualConnectDialog(Ui_OfbQtManualConnectDialog, OfbQtAsyncDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setupUi(self)
        if sys.platform == "win32":
            self.setStyleSheet(WIN32_BODY_STYLE)

        self.names = list(DEVICE_TO_DRIVER_MAP.keys())
        self.profile_picker.addItems(self.names)

    async def get_user_response(self):
        res = await super().get_user_response()
        return res, self.names[self.profile_picker.currentIndex()], self.address_field.text()
