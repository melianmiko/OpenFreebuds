import sys

from PyQt6.QtCore import QLocale
from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds.shortcuts import OfbShortcuts
from openfreebuds.utils.logger import create_logger
from openfreebuds_backend import is_run_at_boot, set_run_at_boot
from openfreebuds_qt.app.module import OfbQtCommonModule
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.designer.ui_settings import Ui_OfbQtUiSettingsModule
from openfreebuds_qt.qt_i18n import get_shortcut_names
from openfreebuds_qt.utils import blocked_signals, list_available_locales

log = create_logger("OfbQtUiSettingsModule")


class OfbQtUiSettingsModule(Ui_OfbQtUiSettingsModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.shortcut_names = get_shortcut_names()
        self.available_shortcuts = OfbShortcuts.all()
        self.available_icons = ["auto", "light", "dark"]
        self.available_updater_policies = ["show", "check", "off"]
        self.available_locales = ["auto", *list_available_locales()]
        self.config = OfbQtConfigParser.get_instance()

        log.info(self.available_shortcuts)
        log.info(self.available_locales)

        self.setupUi(self)
        for shortcut in self.available_shortcuts:
            self.tray_shortcut_picker.addItem(self.shortcut_names.get(shortcut, shortcut))
        for locale in self.available_locales:
            if locale == "auto":
                continue
            name = QLocale(locale).nativeLanguageName()
            self.language_picker.addItem(name)

        with blocked_signals(self.updater_policy_picker):
            if sys.platform == "win32":
                self.updater_policy_picker.setCurrentIndex(
                    self.available_updater_policies.index(self.config.get("updater", "mode", "show"))
                )
            else:
                self.updater_policy_picker.setCurrentIndex(2)
                self.updater_policy_picker.setEnabled(False)
        with blocked_signals(self.tray_shortcut_picker):
            self.tray_shortcut_picker.setCurrentIndex(
                self.available_shortcuts.index(self.config.get("ui", "tray_shortcut", "next_mode"))
            )
        with blocked_signals(self.language_picker):
            self.language_picker.setCurrentIndex(
                self.available_locales.index(self.config.get("ui", "language", "auto"))
            )
        with blocked_signals(self.tray_icon_picker):
            self.tray_icon_picker.setCurrentIndex(
                self.available_icons.index(self.config.get("ui", "tray_icon_theme", "auto"))
            )
        with blocked_signals(self.tray_eq_toggle):
            self.tray_eq_toggle.setChecked(self.config.get("ui", "tray_show_equalizer", False))
        with blocked_signals(self.tray_dc_toggle):
            self.tray_dc_toggle.setChecked(self.config.get("ui", "tray_show_dual_connect", False))
        with blocked_signals(self.autostart_toggle):
            self.autostart_toggle.setChecked(is_run_at_boot())

    @asyncSlot(bool)
    async def on_autostart_toggle(self, value: bool):
        set_run_at_boot(value)

    @asyncSlot(bool)
    async def on_tray_eq_toggle(self, value: bool):
        self.config.set("ui", "tray_show_equalizer", value)
        self.config.save()
        await self.ofb.send_message(OfbEventKind.QT_SETTINGS_CHANGED)

    @asyncSlot(bool)
    async def on_tray_dc_toggle(self, value: bool):
        self.config.set("ui", "tray_show_dual_connect", value)
        self.config.save()
        await self.ofb.send_message(OfbEventKind.QT_SETTINGS_CHANGED)

    @asyncSlot(int)
    async def on_language_choose(self, index: int):
        self.config.set("ui", "language", self.available_locales[index])
        self.config.save()

    @asyncSlot(int)
    async def on_updater_policy_choose(self, index: int):
        self.config.set("updater", "mode", self.available_updater_policies[index])
        self.config.save()

    @asyncSlot(int)
    async def on_tray_color_choose(self, index: int):
        self.config.set("ui", "tray_icon_theme", self.available_icons[index])
        self.config.save()
        await self.ofb.send_message(OfbEventKind.QT_SETTINGS_CHANGED)

    @asyncSlot(int)
    async def on_tray_shortcut_choose(self, index: int):
        self.config.set("ui", "tray_shortcut", self.available_shortcuts[index])
        self.config.save()
