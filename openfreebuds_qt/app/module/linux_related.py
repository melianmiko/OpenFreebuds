import os
import webbrowser

from PyQt6.QtCore import pyqtSlot

from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.designer.linux_extras import Ui_OfbQtLinuxExtrasModule


class OfbQtLinuxExtrasModule(Ui_OfbQtLinuxExtrasModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        # TODO: Impl MPRIS-helper

        if os.environ.get("XDG_SESSION_TYPE") != "wayland":
            self.wayland_root.setVisible(False)

    @pyqtSlot()
    def on_hotkeys_doc(self):
        url = "https://mmk.pw/en/openfreebuds/help"
        webbrowser.open(url)
