import asyncio
import os
import signal
from typing import Optional

from PyQt6.QtWidgets import QApplication
from qasync import asyncSlot

import openfreebuds
from openfreebuds import IOpenFreebuds
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.addons.device_auto_select import OfbQtDeviceAutoSelect
from openfreebuds_qt.app.helper.setting_tab_helper import OfbQtSettingsTabHelper
from openfreebuds_qt.app.main import OfbQtSettingsUi
from openfreebuds_qt.config.config_lock import ConfigLock
from openfreebuds_qt.config.main import OfbQtConfigParser
from openfreebuds_qt.designer.main_window import Ui_OfbMainWindowDesign
from openfreebuds_qt.generic import IOfbQtMainWindow
from openfreebuds_qt.tray.main import OfbTrayIcon

log = create_logger("OfbQtMainWindow")


class OfbQtMainWindow(Ui_OfbMainWindowDesign, IOfbQtMainWindow):
    application: QApplication
    settings: OfbQtSettingsUi

    def __init__(self):
        super().__init__()

        self._exit_started: bool = False
        self.auto_select: Optional[OfbQtDeviceAutoSelect] = None

        self.setupUi(self)
        self.retranslateUi(self)

        self.tabs = OfbQtSettingsTabHelper(self.tabs_list_content, self.body_content)
        self.config = OfbQtConfigParser.get_instance()

    def retranslate_ui(self):
        self.retranslateUi(self)
        self.settings.retranslate_ui()

    @asyncSlot()
    async def on_exit(self):
        await self.exit()

    async def exit(self, ret_code: int = 0):
        await self.tray.close()

        if self.ofb.role == "standalone":
            await self.auto_select.close()
            await self.ofb.stop()

        self.application.closeAllWindows()
        self.application.exit(ret_code)
        ConfigLock.release()

    async def boot(self):
        self.tray = OfbTrayIcon(self)
        self.settings = OfbQtSettingsUi(self.tabs, self.ofb)
        self.auto_select = OfbQtDeviceAutoSelect(self.ofb)

        if self.ofb.role == "standalone":
            await self.restore_device()
            await self.auto_select.boot()

        await self.tray.boot()
        await self.settings.boot()
        self.tray.show()

    async def restore_device(self):
        name = self.config.get("device", "name", None)
        address = self.config.get('device', "address", None)
        if address is not None:
            log.info(f"Restore device name={name}, address={address}")
            await self.ofb.start(name, address)

    def closeEvent(self, e):
        if self.isVisible():
            e.ignore()
            self.hide()
            return

    def showEvent(self, e):
        e.accept()
        self.settings.on_show()

    def hideEvent(self, e):
        e.accept()
        self.settings.on_hide()
