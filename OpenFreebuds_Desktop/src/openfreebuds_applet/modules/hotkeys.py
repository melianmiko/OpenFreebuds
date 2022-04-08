import logging
import os
import traceback
import webbrowser

from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import actions

log = logging.getLogger("HotkeysTool")


class _PynputState:
    current = None


def start(applet):
    if _PynputState.current is not None:
        _PynputState.current.stop()

    if not applet.settings.enable_hotkeys:
        return

    log.debug("Starting hotkey tool...")

    try:
        from pynput.keyboard import GlobalHotKeys
    except ImportError as e:
        info = "Can't import pynput due to {}. Hotkeys won't work".format(e.msg)
        applet.tray_application.message_box(info, "OpenFreebuds Hotkeys")
        return

    if "XDG_SESSION_TYPE" in os.environ:
        if os.environ["XDG_SESSION_TYPE"] == "wayland":
            applet.tray_application.confirm_box(t("hotkeys_wayland"), "OpenFreebuds",
                                                _wayland_callback)

    handlers = actions.get_actions(applet)
    config = applet.settings.hotkeys_config
    merged = {}

    for a in handlers:
        if a in config and config[a] != "":
            merged["<ctrl>+<alt>+" + config[a]] = handlers[a]

    _PynputState.current = GlobalHotKeys(merged)
    _PynputState.current.start()
    log.debug("Started hotkey tool.")


def _wayland_callback(result):
    if result:
        webbrowser.open("https://melianmiko.ru/posts/openfreebuds-faq/")
