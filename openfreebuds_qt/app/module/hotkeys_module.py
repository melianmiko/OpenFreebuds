from PyQt6.QtWidgets import QTableWidgetItem
from qasync import asyncSlot

from openfreebuds.shortcuts import OfbShortcuts
from openfreebuds.utils.logger import create_logger
from openfreebuds_backend import GLOBAL_HOTKEYS_AVAILABLE
from openfreebuds_qt.app.module import OfbQtCommonModule
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.designer.hotkeys import Ui_OfbQtHotkeysModule
from openfreebuds_qt.qt_i18n import get_shortcut_names
from openfreebuds_qt.utils.hotkeys.recorder import OfbQtHotkeyRecorder
from openfreebuds_qt.utils.hotkeys.service import OfbQtHotkeyService
from openfreebuds_qt.utils.qt_utils import qt_error_handler, blocked_signals

log = create_logger("OfbQtHotkeysModule")


class OfbQtHotkeysModule(Ui_OfbQtHotkeysModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.shortcut_names = get_shortcut_names()
        self.service = OfbQtHotkeyService.get_instance(self.ofb)
        self.config = OfbQtConfigParser.get_instance()
        self.recorder = OfbQtHotkeyRecorder()
        self.all_shortcuts = OfbShortcuts.all()

        self.setupUi(self)

        with blocked_signals(self.shortcuts_toggle):
            self.shortcuts_toggle.setChecked(self.config.get("hotkeys", "enabled", False))

        self.table.setEnabled(self.config.get("hotkeys", "enabled", False))
        self.table.setRowCount(len(self.all_shortcuts))
        for index, shortcut in enumerate(self.all_shortcuts):
            self.table.setItem(index, 0, QTableWidgetItem(self.shortcut_names.get(shortcut, shortcut)))
            self.table.setItem(index, 1, QTableWidgetItem(self.config.get("hotkeys", shortcut, "Disabled")))

    @staticmethod
    def available():
        return GLOBAL_HOTKEYS_AVAILABLE

    @asyncSlot(bool)
    async def on_toggle_enabled(self, value: bool):
        async with qt_error_handler("OfbQtHotkeysModule_GlobalSwitch", self.ctx):
            self.config.set("hotkeys", "enabled", value)
            self.config.save()
            self.table.setEnabled(value)

            self.service.stop()
            self.service.start()

    @asyncSlot(int, int)
    async def on_edit_shortcut(self, index: int, column: int):
        if column != 1:
            return

        async with qt_error_handler("OfbQtHotkeysModule_EditShortcut", self.ctx):
            shortcut = self.all_shortcuts[index]
            log.info(f"Editing {shortcut}")
            self.table.setItem(index, column, QTableWidgetItem(self.tr("Press new shortcut…")))

            self.service.stop()
            r = await self.recorder.record()
            if r:
                self.config.set("hotkeys", shortcut, r)
            else:
                self.config.remove("hotkeys", shortcut)
            self.config.save()
            self.service.start()

            self.table.setItem(index, column, QTableWidgetItem(self.config.get("hotkeys", shortcut, "Disabled")))
