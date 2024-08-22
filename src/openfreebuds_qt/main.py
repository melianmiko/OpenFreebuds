from PyQt6.QtWidgets import QApplication
from qasync import asyncClose

import openfreebuds
from openfreebuds_qt.generic import IOfbQtMainWindow
from openfreebuds_qt.tray.main import OfbTrayIcon


class OfbQtMainWindow(IOfbQtMainWindow):
    application: QApplication

    async def exit(self, ret_code: int = 0):
        await self.tray.close()

        if self.ofb.role == "standalone":
            await self.ofb.stop()

        self.application.closeAllWindows()
        self.application.exit(ret_code)

    async def boot(self):
        self.ofb = await openfreebuds.create()

        self.tray = OfbTrayIcon(self)
        await self.tray.boot()
        self.tray.show()

    # @asyncClose
    # async def closeEvent(self, event):
    #     event.accept()
    #     await self.exit()
