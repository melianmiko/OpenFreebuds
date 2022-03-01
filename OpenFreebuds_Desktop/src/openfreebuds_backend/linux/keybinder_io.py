import logging
import os
import webbrowser

import gi

from openfreebuds_applet.l18n import t
from openfreebuds_backend.linux import ui_gtk

log = logging.getLogger("LinuxBackend")
gi.require_version('Keybinder', '3.0')


class KeybinderState:
    init_complete = False
    current_hotkeys = []


def bind_hotkeys(keys):
    from gi.repository import Keybinder
    _init_keybinder()
    stop_hotkeys()

    # Add new key bindings
    for a in keys:
        key_string = "<Ctrl><Alt>" + a
        Keybinder.bind(key_string, keys[a])

        KeybinderState.current_hotkeys.append(key_string)
        log.debug("Added hotkey " + key_string)


def stop_hotkeys():
    from gi.repository import Keybinder

    # Remove all exiting key bindings
    for a in KeybinderState.current_hotkeys:
        Keybinder.unbind(a)
        log.debug("Removed hotkey " + a)

    KeybinderState.current_hotkeys = []


def _init_keybinder():
    from gi.repository import Keybinder
    if KeybinderState.init_complete:
        return

    if "XDG_SESSION_TYPE" in os.environ:
        if os.environ["XDG_SESSION_TYPE"] == "wayland":
            ui_gtk.ask_question(t("hotkeys_wayland"), callback=_wayland_warn_callback)

    Keybinder.init()
    KeybinderState.init_complete = True


def _wayland_warn_callback(result):
    if result:
        webbrowser.open("https://melianmiko.ru/posts/openfreebuds-wayland/")
