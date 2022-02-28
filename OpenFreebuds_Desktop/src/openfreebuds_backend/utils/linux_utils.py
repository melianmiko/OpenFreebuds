import logging
import os
import pathlib
import sys

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