from PyQt6.QtWidgets import QWidget, QApplication

import openfreebuds
from openfreebuds_qt.async_qt_loop import qt_app_entrypoint
from openfreebuds_qt.tray.main import OfbTrayIcon


@qt_app_entrypoint
async def main(_: QApplication, window: QWidget):
    window.show()

    manager = await openfreebuds.create()

    tray = OfbTrayIcon(window, manager)
    await tray.boot()

    tray.show()
