import os
import webbrowser

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMessageBox
from qasync import asyncSlot

from openfreebuds import STORAGE_PATH
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.config.feature import OfbQtFeatureAvailability
from openfreebuds_qt.constants import LINK_WEBSITE_HELP
from openfreebuds_qt.designer.linux_extras import Ui_OfbQtLinuxExtrasModule
from openfreebuds_qt.utils import blocked_signals
from openfreebuds_qt.utils.mpris.service import OfbQtMPRISHelperService


class OfbQtLinuxExtrasModule(Ui_OfbQtLinuxExtrasModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = OfbQtConfigParser.get_instance()
        self.service = OfbQtMPRISHelperService.get_instance(self.ofb)

        self.setupUi(self)
        with blocked_signals(self.mpris_helper_checkbox):
            self.mpris_helper_checkbox.setChecked(self.config.get("mpris", "enabled", False))
        with blocked_signals(self.force_x11_checkbox):
            self.force_x11_checkbox.setChecked((STORAGE_PATH / "force_xorg").is_file())

        if os.environ.get("XDG_SESSION_TYPE") != "wayland":
            self.wayland_root.setVisible(False)

    @pyqtSlot()
    def on_hotkeys_doc(self):
        webbrowser.open(LINK_WEBSITE_HELP)

    @asyncSlot(bool)
    async def on_force_x11_toggle(self, value: bool):
        file = STORAGE_PATH / "force_xorg"
        if value:
            with open(file, "w") as f:
                f.write("ON")
        else:
            file.unlink(missing_ok=True)

    @asyncSlot(bool)
    async def on_mpris_toggle(self, value: bool):
        if value and OfbQtFeatureAvailability.is_flatpak():
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
