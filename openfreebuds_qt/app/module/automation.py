from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QComboBox

from openfreebuds.shortcuts import OfbShortcuts
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.designer.automation_module import Ui_OfbQtAutomationModule
from openfreebuds_qt.qt_i18n import get_shortcut_names

log = create_logger("OfbQtAutomationModule")


class OfbQtAutomationModule(Ui_OfbQtAutomationModule, OfbQtCommonModule):
    banned_shortcuts = ["connect", "disconnect", "toggle_connect"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = OfbQtConfigParser.get_instance()
        self.shortcut_names = get_shortcut_names()
        self.available_shortcuts = [
            False,
            *[x for x in OfbShortcuts.all() if x not in self.banned_shortcuts]
        ]

        self.setupUi(self)

        self._setup_select("on_connect", self.on_connect_action)
        self._setup_select("on_disconnect", self.on_disconnect_action)

    def _setup_select(self, prop_name: str, select_box: QComboBox):
        @pyqtSlot(int)
        def _activate(index: int):
            action_name = self.available_shortcuts[index]
            self.config.set("automation", prop_name, action_name)

        for shortcut in self.available_shortcuts:
            select_box.addItem(self.shortcut_names.get(shortcut, shortcut) or self.tr("Disabled"))

        select_box.setCurrentText(
            self.config.get("automation", prop_name, self.tr("Disabled"))
        )

        select_box.currentIndexChanged[int].connect(_activate)
