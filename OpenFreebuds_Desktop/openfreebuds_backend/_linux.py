import logging
import os

import dbus
import pystray._appindicator
import pystray._base
from dbus.mainloop.glib import DBusGMainLoop

from openfreebuds_applet.l18n import t

DBusGMainLoop(set_as_default=True)

# Yes, this isn't good practise, but this reduces count
# of imported package and force set backend to app indicator
Menu = pystray._base.Menu
MenuItem = pystray._base.MenuItem
TrayIcon = pystray._appindicator.Icon

UI_RESULT_YES = -8
UI_RESULT_NO = -9

log = logging.getLogger("LinuxBackend")


def bind_hotkeys(keys):
    if "XDG_SESSION_TYPE" in os.environ:
        if os.environ["XDG_SESSION_TYPE"] == "wayland":
            show_message(t("hotkeys_wayland"), "OpenFreebuds")

    import gi
    gi.require_version('Keybinder', '3.0')
    from gi.repository import Keybinder
    Keybinder.init()
    for a in keys:
        key_string = "<Ctrl><Alt>" + a
        Keybinder.bind(key_string, keys[a])
        log.debug("Added hotkey " + key_string)


def bt_is_connected(address):
    try:
        system = dbus.SystemBus()
        bluez = dbus.Interface(system.get_object("org.bluez", "/"),
                               "org.freedesktop.DBus.ObjectManager")

        all_objects = bluez.GetManagedObjects()

        for path in all_objects:
            if "org.bluez.Device1" in all_objects[path]:
                device = dbus.Interface(system.get_object("org.bluez", path),
                                        "org.freedesktop.DBus.Properties")
                props = _dbus_to_python(device.GetAll("org.bluez.Device1"))
                if props.get("Address", "") == address:
                    return props.get("Connected", False)
    except dbus.exceptions.DBusException:
        log.exception("Failed to check connection state")

    return None


def bt_device_exists(address):
    return bt_is_connected(address) is not None


def bt_list_devices():
    scan_results = []

    try:
        system = dbus.SystemBus()
        bluez = dbus.Interface(system.get_object("org.bluez", "/"),
                               "org.freedesktop.DBus.ObjectManager")

        all_objects = bluez.GetManagedObjects()

        for path in all_objects:
            if "org.bluez.Device1" in all_objects[path]:
                device = dbus.Interface(system.get_object("org.bluez", path),
                                        "org.freedesktop.DBus.Properties")
                props = _dbus_to_python(device.GetAll("org.bluez.Device1"))

                if props.get("Name", "") == "":
                    continue

                scan_results.append({
                    "name": props.get("Name", ""),
                    "address": props.get("Address", "Unknown address"),
                    "connected": props.get("Connected", False)
                })
    except dbus.exceptions.DBusException:
        log.exception("Failed to list devices")

    return scan_results


# noinspection PyArgumentList
def show_message(message, window_title=""):
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,
                            Gtk.ButtonsType.OK, window_title)
    msg.format_secondary_text(message)
    msg.run()
    msg.destroy()


# noinspection PyArgumentList
def ask_question(message, window_title=""):
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,
                            Gtk.ButtonsType.YES_NO, window_title)
    msg.format_secondary_text(message)
    result = msg.run()
    msg.destroy()

    return result


# noinspection PyArgumentList
def ask_string(message, window_title="", current_value=""):
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK_CANCEL, window_title)
    dialog.format_secondary_text(message)

    area = dialog.get_content_area()
    entry = Gtk.Entry()
    entry.set_margin_start(16)
    entry.set_margin_end(16)
    entry.set_text(current_value)
    area.pack_end(entry, False, False, 0)
    dialog.show_all()

    response = dialog.run()
    text = entry.get_text()
    dialog.destroy()

    if response == Gtk.ResponseType.OK:
        return text

    return None


def is_dark_theme():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    settings = Gtk.Settings.get_default()
    theme_name = settings.get_property("gtk-theme-name")
    return "Dark" in theme_name


# From https://stackoverflow.com/questions/11486443/dbus-python-how-to-get-response-with-native-types
def _dbus_to_python(data):
    """convert dbus data types to python native data types"""
    if isinstance(data, dbus.String):
        data = str(data)
    elif isinstance(data, dbus.Boolean):
        data = bool(data)
    elif isinstance(data, dbus.Int64):
        data = int(data)
    elif isinstance(data, dbus.Double):
        data = float(data)
    elif isinstance(data, dbus.Array):
        data = [_dbus_to_python(value) for value in data]
    elif isinstance(data, dbus.Dictionary):
        new_data = dict()
        for key in data.keys():
            new_key = _dbus_to_python(key)
            new_data[new_key] = _dbus_to_python(data[key])
        data = new_data
    return data
