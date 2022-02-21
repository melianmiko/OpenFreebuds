import logging
import os

from pynput import keyboard

from openfreebuds_applet import platform_tools
from openfreebuds_applet.l18n import t

log = logging.getLogger("HotkeysTool")


def start(applet):
    OpenFreebudsHotkeyTool(applet).start()


class OpenFreebudsHotkeyTool:
    def __init__(self, applet):
        self._applet = applet
        self.hotkeys = {}
        self.load_hotkeys()

    def load_hotkeys(self):
        settings = self._applet.settings

        if not settings.enable_hotkeys:
            return

        if settings.hotkey_next_mode != "":
            self.hotkeys[settings.hotkey_next_mode] = self.do_next_mode

    def do_next_mode(self):
        dev = self._get_device()
        if dev is not None:
            current = dev.get_property("noise_mode", -99)
            if current == -99:
                return
            next_mode = (current + 1) % 3
            dev.set_property("noise_mode", next_mode)
            log.debug("Switched to mode " + str(next_mode))

    def _get_device(self):
        manager = self._applet.manager
        if manager.state != manager.STATE_CONNECTED:
            log.debug("Hotkey ignored, no device")
            return None

        return manager.device

    def start(self):
        if len(self.hotkeys) == 0:
            return

        if os.environ["XDG_SESSION_TYPE"] == "wayland":
            platform_tools.show_message(t("hotkeys_wayland"), "OpenFreebuds")

        log.debug("Starting hotkey tool...")
        l = keyboard.GlobalHotKeys(self.hotkeys)
        l.start()
        log.debug("Started hotkey tool.")
