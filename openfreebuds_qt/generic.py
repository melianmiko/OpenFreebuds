from PyQt6.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon

from openfreebuds import IOpenFreebuds


class IOfbMainWindow(QMainWindow):
    async def boot(self):
        raise NotImplementedError("Not implemented")


class IOfbTrayIcon(QSystemTrayIcon):
    """
    Generic model for OpenFreebuds Tray Icon
    """

    async def boot(self):
        raise NotImplementedError("Not implemented")

    async def close(self):
        raise NotImplementedError("Not implemented")


class IOfbQtApplication(QApplication):
    qt_app: QApplication = super(QApplication)
    main_window: IOfbMainWindow
    ofb: IOpenFreebuds
    tray: IOfbTrayIcon

    async def exit(self, ret_code: int = 0):
        raise NotImplementedError("Not implemented")
