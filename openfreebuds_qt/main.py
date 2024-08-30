from typing import Optional

from PyQt6.QtWidgets import QMenu
from qasync import asyncSlot

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.addons.device_auto_select import OfbQtDeviceAutoSelect
from openfreebuds_qt.app.dialog.manual_connect import OfbQtManualConnectDialog
from openfreebuds_qt.app.helper.setting_tab_helper import OfbQtSettingsTabHelper
from openfreebuds_qt.app.main import OfbQtSettingsUi
from openfreebuds_qt.app.qt_utils import qt_error_handler
from openfreebuds_qt.config.config_lock import ConfigLock
from openfreebuds_qt.config.main import OfbQtConfigParser
from openfreebuds_qt.designer.main_window import Ui_OfbMainWindowDesign
from openfreebuds_qt.generic import IOfbQtContext
from openfreebuds_qt.icon.qt_icon import get_qt_icon_colored
from openfreebuds_qt.tray.main import OfbTrayIcon

log = create_logger("OfbQtMainWindow")


class OfbQtMainWindow(Ui_OfbMainWindowDesign, IOfbQtContext):
    settings: OfbQtSettingsUi

    def __init__(self):
        super().__init__()

        self._exit_started: bool = False
        self.auto_select: Optional[OfbQtDeviceAutoSelect] = None

        self.setupUi(self)
        self.retranslateUi(self)

        # Extras button
        self.extra_options_button.setIcon(
            get_qt_icon_colored("settings", self.palette().text().color().getRgb())
        )

        self.extra_menu = QMenu()
        self.extra_options_button.setMenu(self.extra_menu)
        self._fill_extras_menu()

        self.tabs = OfbQtSettingsTabHelper(self.tabs_list_content, self.body_content)
        self.config = OfbQtConfigParser.get_instance()

    # noinspection PyUnresolvedReferences
    def _fill_extras_menu(self):
        self.extra_menu.addAction(self.tr("Temporary replace device")).triggered.connect(self.temporary_change_device)
        self.extra_menu.addAction(self.tr("Close application")).triggered.connect(self.on_exit)

    async def exit(self, ret_code: int = 0):
        await self.tray.close()

        if self.ofb.role == "standalone":
            await self.auto_select.close()
            await self.ofb.destroy()

        self.application.closeAllWindows()
        self.application.exit(ret_code)
        ConfigLock.release()

    async def boot(self):
        async with qt_error_handler("OfbQtMain_Boot", self):
            self.tray = OfbTrayIcon(self)
            self.settings = OfbQtSettingsUi(self.tabs, self)
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

    @asyncSlot()
    async def temporary_change_device(self):
        async with qt_error_handler("OfbQtMain_TempConnect", self):
            result, name, address = await OfbQtManualConnectDialog(self).get_user_response()
            if not result:
                return
            await self.ofb.start(name, address)

    def retranslate_ui(self):
        self.retranslateUi(self)
        self.settings.retranslate_ui()

    @asyncSlot()
    async def on_exit(self):
        async with qt_error_handler("OfbQtMain_OnExit", self):
            await self.exit()

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
