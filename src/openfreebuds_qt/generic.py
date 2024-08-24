from PyQt6.QtWidgets import QMainWindow

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.tray.generic import IOfbTrayIcon


class IOfbQtMainWindow(QMainWindow):
    ofb: IOpenFreebuds
    tray: IOfbTrayIcon

    async def boot(self):
        raise NotImplementedError("Not implemented")

    async def exit(self, ret_code: int = 0):
        raise NotImplementedError("Not implemented")
