import logging
import os
import pathlib
import subprocess

import dbus

from openfreebuds import event_bus
from openfreebuds.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_backend.utils import linux_utils
from openfreebuds_applet.l18n import t

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


def is_run_at_boot():
    return os.path.isfile(linux_utils.get_autostart_file_path())


def set_run_at_boot(val):
    path = linux_utils.get_autostart_file_path()
    data = linux_utils.mk_autostart_file_content()

    if val:
        # Install
        with open(path, "w") as f:
            f.write(data)
        log.debug("Created autostart file: " + path)
    else:
        # Remove
        if os.path.isfile(path):
            os.unlink(path)
        log.debug("Removed autostart file: " + path)
        
    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


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


def show_message(message, window_title="", is_error=False):
    from gi.repository import GLib
    GLib.idle_add(lambda: linux_utils.gtk_show_message(message, window_title, is_error))


# noinspection PyArgumentList
def ask_question(message, callback, window_title=""):
    from gi.repository import GLib
    GLib.idle_add(lambda: linux_utils.gtk_ask_question(message, callback, window_title))


# noinspection PyArgumentList
def ask_string(message, callback, window_title="", current_value=""):
    from gi.repository import GLib
    GLib.idle_add(lambda: linux_utils.gtk_ask_string(message, callback, window_title, current_value))


def is_dark_theme():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    settings = Gtk.Settings()
    defaults = settings.get_default()
    theme_name = defaults.get_property("gtk-theme-name")
    return "Dark" in theme_name
