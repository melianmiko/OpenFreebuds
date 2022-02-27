import logging
import os
import pathlib
import subprocess

import dbus

from openfreebuds_backend.utils import linux_utils
from openfreebuds_applet.l18n import t

UI_RESULT_YES = -8
UI_RESULT_NO = -9

log = logging.getLogger("LinuxBackend")


def get_app_storage_path():
    return pathlib.Path.home() / ".config"


def open_in_file_manager(path):
    subprocess.Popen(["xdg-open", path])


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
        path = linux_utils.dbus_find_bt_device(address)
        if path is None:
            return None

        system = dbus.SystemBus()
        device = dbus.Interface(system.get_object("org.bluez", path),
                                "org.freedesktop.DBus.Properties")
        props = linux_utils.dbus_to_python(device.GetAll("org.bluez.Device1"))
        return props.get("Connected", False)
    except dbus.exceptions.DBusException:
        log.exception("Failed to check connection state")

    return None


def bt_device_exists(address):
    return bt_is_connected(address) is not None


def bt_connect(address):
    try:
        path = linux_utils.dbus_find_bt_device(address)
        if path is None:
            return False

        system = dbus.SystemBus()
        device = dbus.Interface(system.get_object("org.bluez", path),
                                "org.bluez.Device1")
        device.Connect()
        return True
    except dbus.exceptions.DBusException:
        log.exception("Failed to check connection state")
        return False


def bt_disconnect(address):
    try:
        path = linux_utils.dbus_find_bt_device(address)
        if path is None:
            return False

        system = dbus.SystemBus()
        device = dbus.Interface(system.get_object("org.bluez", path),
                                "org.bluez.Device1")
        device.Disconnect()
        return True
    except dbus.exceptions.DBusException:
        log.exception("Failed to check connection state")
        return False


def bt_list_devices():
    return linux_utils.dbus_list_bt_devices()


def get_system_id():
    if os.path.isfile("/usr/bin/dpkg"):
        return ["debian", "linux"]
    else:
        return ["linux"]


# noinspection PyArgumentList
def show_message(message, window_title="", is_error=False):
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    msg_type = Gtk.MessageType.INFO
    if is_error:
        msg_type = Gtk.MessageType.ERROR

    msg = Gtk.MessageDialog(None, 0, msg_type, Gtk.ButtonsType.OK, window_title)
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

    settings = Gtk.Settings()
    defaults = settings.get_default()
    theme_name = defaults.get_property("gtk-theme-name")
    return "Dark" in theme_name
