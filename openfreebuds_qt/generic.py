from PyQt6.QtWidgets import QMainWindow, QApplication

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.tray.generic import IOfbTrayIcon


class IOfbQtContext(QMainWindow):
    application: QApplication
    ofb: IOpenFreebuds
    tray: IOfbTrayIcon

    async def exit(self, ret_code: int = 0):
        raise NotImplementedError("Not implemented")
