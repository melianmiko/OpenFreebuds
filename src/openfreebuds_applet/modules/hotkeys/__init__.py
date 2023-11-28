import logging
import tkinter

from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import GenericModule
from openfreebuds_applet.modules.actions import get_actions
from openfreebuds_applet.modules.hotkeys._settings import HotkeysSettings
from openfreebuds_applet.ui import tk_tools

log = logging.getLogger("HotkeysTool")


class Module(GenericModule):
    ident = "hotkeys"
    name = t("settings_tab_hotkeys")
    description = t("hotkeys_info")
    order = 0
    def_settings = {
        "enabled": True,
        "next_mode": "<ctrl>+<alt>+q"
    }

    def __init__(self):
        super().__init__()
        self.pynput = None

    def stop(self):
        if self.pynput is not None:
            self.pynput.stop()
        log.info("Stopped")

    @staticmethod
    def test_available():
        try:
            from pynput import keyboard
            return True, ""
        except ImportError as e:
            return False, str(e)

    def make_settings_frame(self, parent: tkinter.BaseWidget) -> HotkeysSettings:
        return HotkeysSettings(parent, self)

    def start(self):
        if self.pynput is not None:
            self.pynput.stop()

        if not self.test_available()[0]:
            log.error("Can't start hotkeys tool: service don't available")
            return

        log.debug("Starting hotkey tool...")

        from pynput.keyboard import GlobalHotKeys
        handlers = get_actions(self.app_manager)
        config = self.settings
        merged = {}

        for a in handlers:
            if a in config and config[a] != "":
                merged[config[a]] = handlers[a]

        try:
            self.pynput = GlobalHotKeys(merged)
            self.pynput.start()
            log.debug("Started hotkey tool.")
        except ValueError:
            log.exception("Can't start GlobalHotKeys")
            tk_tools.message("Can't bind hotkeys due to error")
