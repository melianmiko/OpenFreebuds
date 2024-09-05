import webbrowser

from PyQt6.QtWidgets import QWidget

from openfreebuds_qt.utils.async_dialog import OfbQtAsyncDialog
from openfreebuds_qt.designer.dependency_missing import Ui_OfbQtDependencyMissingDialog


class OfbQtDependencyMissingDialog(Ui_OfbQtDependencyMissingDialog, OfbQtAsyncDialog):
    def __init__(self, parent: QWidget, args: list):
        super().__init__(parent)

        self.setupUi(self)
        self.info_view.setText(args[0])
        self.url = args[1]

    async def get_user_response(self):
        result = await super().get_user_response()
        if result:
            webbrowser.open(self.url)
