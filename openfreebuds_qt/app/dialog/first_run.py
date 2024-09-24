import sys
import webbrowser

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QDialog
from qasync import asyncSlot

import openfreebuds_backend
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.constants import LINK_WEBSITE_HELP
from openfreebuds_qt.designer.first_run_dialog import Ui_OfbQtFirstRunDialog
from openfreebuds_qt.utils import get_img_colored, qt_error_handler


class OfbQtFirstRunDialog(Ui_OfbQtFirstRunDialog, QDialog):
    def __init__(self, ctx):
        super().__init__(ctx.main_window)

        self.ctx = ctx
        self.config = OfbQtConfigParser.get_instance()

        self.setupUi(self)

        self.autostart_checkbox.setChecked(self.config.is_containerized_app)
        self.autostart_checkbox.setEnabled(not self.config.is_containerized_app)
        self.linux_notice.setVisible(sys.platform == 'linux')

        preview_fn = "ofb_linux_preview" if sys.platform == 'linux' else "ofb_win32_preview"
        preview_image = get_img_colored(preview_fn,
                                        color=self.palette().text().color().getRgb(),
                                        base_dir="image")
        self.preview_root.setPixmap(preview_image)

    @asyncSlot()
    async def on_confirm(self):
        async with qt_error_handler("OfbQtFirstRunDialog_Confirm", self.ctx):
            self.hide()

            if self.autostart_checkbox.isChecked():
                openfreebuds_backend.set_run_at_boot(True)

            self.config.set("ui", "first_run_finished", True)
            self.config.save()

    @pyqtSlot()
    def on_faq_click(self):
        webbrowser.open(LINK_WEBSITE_HELP)
