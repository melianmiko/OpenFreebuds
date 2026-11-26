from PyQt6.QtWidgets import QWidget

from openfreebuds.driver.utils import get_display_device_names
from openfreebuds_qt.utils.async_dialog import OfbQtAsyncDialog
from openfreebuds_qt.designer.dialog_profile_picker import Ui_Dialog


class OfbQtProfilePickerDialog(Ui_Dialog, OfbQtAsyncDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setupUi(self)

        self.names = get_display_device_names()
        self.profile_picker.addItems(self.names)

    async def get_user_response(self):
        res = await super().get_user_response()
        return res, self.names[self.profile_picker.currentIndex()]
