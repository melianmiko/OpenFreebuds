import sys
import webbrowser

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QDialog, QSystemTrayIcon
from qasync import asyncSlot

import openfreebuds_backend
from openfreebuds import OfbEventKind
from openfreebuds_backend import AUTOSTART_AVAILABLE, is_run_at_boot
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.constants import LINK_WEBSITE_HELP
from openfreebuds_qt.constants import WIN32_BODY_STYLE
from openfreebuds_qt.designer.first_run_dialog import Ui_OfbQtFirstRunDialog
from openfreebuds_qt.utils import get_img_colored, qt_error_handler


class OfbQtFirstRunDialog(Ui_OfbQtFirstRunDialog, QDialog):
    def __init__(self, ctx):
        super().__init__(ctx.main_window)

        self.ctx = ctx
        self.config = OfbQtConfigParser.get_instance()
        self.is_first_run = not self.config.get("ui", "first_run_finished", False)

        self.setupUi(self)
        if sys.platform == "win32":
            self.setStyleSheet(WIN32_BODY_STYLE)

        tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        if self.is_first_run:
            background_enabled = tray_available
            autostart_enabled = AUTOSTART_AVAILABLE
        else:
            background_enabled = tray_available and self.config.get("ui", "background", True)
            try:
                autostart_enabled = AUTOSTART_AVAILABLE and is_run_at_boot()
            except Exception:
                autostart_enabled = False

        self.background_checkbox.setChecked(background_enabled)
        self.background_checkbox.setEnabled(tray_available)

        self.autostart_checkbox.setChecked(autostart_enabled)
        self.autostart_checkbox.setEnabled(AUTOSTART_AVAILABLE)

        preview_fn = "ofb_win32_preview" if sys.platform == "win32" else "ofb_linux_preview"
        preview_image = get_img_colored(preview_fn,
                                        color=self.palette().text().color().getRgb(),
                                        base_dir="image")
        self.preview_root.setPixmap(preview_image)

    @asyncSlot()
    async def on_confirm(self):
        async with qt_error_handler("OfbQtFirstRunDialog_Confirm", self.ctx):
            self.hide()

            await openfreebuds_backend.set_run_at_boot(self.autostart_checkbox.isChecked())
            self.config.set("ui", "background", self.background_checkbox.isChecked())
            self.config.set("ui", "first_run_finished", True)
            self.config.save()

            if not self.background_checkbox.isChecked():
                self.ctx.main_window.show()

            await self.ctx.ofb.send_message(OfbEventKind.QT_SETTINGS_CHANGED)

    @pyqtSlot()
    def on_faq_click(self):
        webbrowser.open(LINK_WEBSITE_HELP)
