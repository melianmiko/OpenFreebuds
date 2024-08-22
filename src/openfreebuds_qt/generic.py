from PyQt6.QtWidgets import QWidget

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.tray.generic import IOfbTrayIcon


class IOfbQtMainWindow(QWidget):
    ofb: IOpenFreebuds
    tray: IOfbTrayIcon

    async def boot(self):
        raise NotImplementedError("Not implemented")

    async def exit(self, ret_code: int = 0):
        raise NotImplementedError("Not implemented")
