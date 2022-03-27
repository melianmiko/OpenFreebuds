import logging
import os
import webbrowser

import gi

from openfreebuds_applet.l18n import t

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


# noinspection PyArgumentList
def _wayland_warning():
    from gi.repository import Gtk
    msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.YES_NO, "OpenFreebuds")
    msg.format_secondary_text(t("hotkeys_wayland"))
    result = msg.run()
    msg.destroy()

    if result == -8:
        webbrowser.open("https://melianmiko.ru/posts/openfreebuds-faq/")


def _init_keybinder():
    from gi.repository import Keybinder, GLib

    if KeybinderState.init_complete:
        return

    if "XDG_SESSION_TYPE" in os.environ:
        if os.environ["XDG_SESSION_TYPE"] == "wayland":
            GLib.idle_add(_wayland_warning)

    Keybinder.init()
    KeybinderState.init_complete = True
