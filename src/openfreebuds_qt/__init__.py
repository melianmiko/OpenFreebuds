from PyQt6.QtWidgets import QApplication

from openfreebuds_qt.async_qt_loop import qt_app_entrypoint
from openfreebuds_qt.main import OfbQtMainWindow


@qt_app_entrypoint(OfbQtMainWindow)
async def main(app: QApplication, window: OfbQtMainWindow):
    window.application = app

    await window.boot()
    window.show()
