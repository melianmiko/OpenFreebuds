import os
import webbrowser

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMessageBox
from qasync import asyncSlot

from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.constants import LINK_WEBSITE_HELP
from openfreebuds_qt.designer.linux_extras import Ui_OfbQtLinuxExtrasModule
from openfreebuds_backend import is_run_at_boot, set_run_at_boot
from openfreebuds_qt.utils import blocked_signals, exec_msg_box_async, qt_error_handler
from openfreebuds_qt.utils.appimage import appimage_path, install, install_path, is_installed, relaunch, \
    uninstall
from openfreebuds_qt.utils.mpris.service import OfbQtMPRISHelperService


class OfbQtLinuxExtrasModule(Ui_OfbQtLinuxExtrasModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = OfbQtConfigParser.get_instance()
        self.service = OfbQtMPRISHelperService.get_instance(self.ofb)

        self.setupUi(self)
        with blocked_signals(self.mpris_helper_checkbox):
            self.mpris_helper_checkbox.setChecked(self.config.get("mpris", "enabled", False))

        if os.environ.get("XDG_SESSION_TYPE") != "wayland":
            self.wayland_root.setVisible(False)

        self.appimage_root.setVisible(appimage_path() is not None)
        self._update_appimage_ui()

    def _update_appimage_ui(self):
        if is_installed():
            self.appimage_status.setText(self.tr("Installed to {}").format(install_path()))
            self.appimage_button.setText(self.tr("Uninstall"))
        else:
            self.appimage_status.setText(self.tr("Install to copy OpenFreebuds to {} and add it to the "
                                                 "application menu.").format(install_path().parent))
            self.appimage_button.setText(self.tr("Install"))

    @asyncSlot()
    async def on_appimage_button(self):
        async with qt_error_handler("OfbQtLinuxExtrasModule_AppImage", self.ctx):
            if not is_installed():
                target = install()
                await exec_msg_box_async(QMessageBox(QMessageBox.Icon.Information,
                                                     "OpenFreebuds",
                                                     self.tr("Installed. OpenFreebuds will restart from {}.")
                                                     .format(target),
                                                     QMessageBox.StandardButton.Ok, self))
                relaunch(target)
                await self.ctx.exit()
                return

            box = QMessageBox(QMessageBox.Icon.Question,
                              "OpenFreebuds",
                              self.tr("Remove OpenFreebuds from {} and from the application menu? "
                                      "The application will close.").format(install_path().parent),
                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
            if await exec_msg_box_async(box) != QMessageBox.StandardButton.Yes:
                return
            if is_run_at_boot():
                await set_run_at_boot(False)
            uninstall()
            await self.ctx.exit()

    @pyqtSlot()
    def on_hotkeys_doc(self):
        webbrowser.open(LINK_WEBSITE_HELP)

    @asyncSlot(bool)
    async def on_mpris_toggle(self, value: bool):
        if value and os.path.isfile("/app/is_container"):
            QMessageBox(
                QMessageBox.Icon.Information,
                self.tr("Ensure bus access"),
                self.tr("Looks like you're running under Flatpak. To use this feature, OpenFreebuds "
                        "need to have access to entire session bus, otherwise it won't find any "
                        "working media players. Ensure that you're granted this permission, "
                        "refer to FAQ for more details."),
                QMessageBox.StandardButton.Ok,
                self
            ).show()

        self.config.set("mpris", "enabled", value)
        self.config.save()
        await self.service.start()
