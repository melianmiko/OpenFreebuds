import logging
import pathlib

import dbus
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

log = logging.getLogger("LinuxBackend")


def get_autostart_file_path():
    autostart_dir = pathlib.Path.home() / ".config/autostart"
    if not autostart_dir.exists():
        autostart_dir.mkdir()
    return str(autostart_dir / "openfreebuds.desktop")


def mk_autostart_file_content():
    return (f"[Desktop Entry]\n"
            f"Name=Openfreebuds\n"
            f"Categories=GNOME;GTK;Utility;\n"
            f"Exec=/usr/bin/openfreebuds\n"
            f"Icon=/opt/openfreebuds/openfreebuds_assets/icon.png\n"
            f"Terminal=false\n"
            f"Type=Application\n"
            f"X-GNOME-Autostart-enabled=true\n")


def dbus_list_bt_devices():
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
                props = dbus_to_python(device.GetAll("org.bluez.Device1"))

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


def dbus_find_bt_device(address):
    try:
        system = dbus.SystemBus()
        bluez = dbus.Interface(system.get_object("org.bluez", "/"),
                               "org.freedesktop.DBus.ObjectManager")

        all_objects = bluez.GetManagedObjects()

        for path in all_objects:
            if "org.bluez.Device1" in all_objects[path]:
                device_props = dbus.Interface(system.get_object("org.bluez", path),
                                              "org.freedesktop.DBus.Properties")
                props = dbus_to_python(device_props.GetAll("org.bluez.Device1"))
                if props.get("Address", "") == address:
                    return path
    except dbus.exceptions.DBusException:
        return None


def gtk_show_message(message, window_title="", is_error=False):
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


def gtk_ask_question(message, callback, window_title=""):
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,
                            Gtk.ButtonsType.YES_NO, window_title)
    msg.format_secondary_text(message)
    result = msg.run() == -8
    msg.destroy()

    callback(result)


# From https://stackoverflow.com/questions/11486443/dbus-python-how-to-get-response-with-native-types
def dbus_to_python(data):
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
        data = [dbus_to_python(value) for value in data]
    elif isinstance(data, dbus.Dictionary):
        new_data = dict()
        for key in data.keys():
            new_key = dbus_to_python(key)
            new_data[new_key] = dbus_to_python(data[key])
        data = new_data
    return data


def gtk_ask_string(message, callback, window_title, current_value):
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

    if response != Gtk.ResponseType.OK:
        text = None

    callback(text)
