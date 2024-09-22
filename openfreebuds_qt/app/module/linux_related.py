import os
import webbrowser

from PyQt6.QtCore import pyqtSlot
from qasync import asyncSlot

from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.config import OfbQtConfigParser
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
        if os.environ.get("XDG_SESSION_TYPE") != "wayland":
            self.wayland_root.setVisible(False)

    @pyqtSlot()
    def on_hotkeys_doc(self):
        webbrowser.open(LINK_WEBSITE_HELP)

    @asyncSlot(bool)
    async def on_mpris_toggle(self, value: bool):
        self.config.set("mpris", "enabled", value)
        self.config.save()
        await self.service.start()
