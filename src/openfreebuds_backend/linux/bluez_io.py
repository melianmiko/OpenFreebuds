import logging

import dbus
from dbus.mainloop.glib import DBusGMainLoop

log = logging.getLogger("LinuxBackend")
DBusGMainLoop(set_as_default=True)


def bt_is_connected(address):
    try:
        path = _dbus_find_bt_device(address)
        if path is None:
            return None

        system = dbus.SystemBus()
        device = dbus.Interface(system.get_object("org.bluez", path),
                                "org.freedesktop.DBus.Properties")
        props = _dbus_to_python(device.GetAll("org.bluez.Device1"))
        return props.get("Connected", False)
    except dbus.exceptions.DBusException:
        log.exception("Failed to check connection state")

    return None


def bt_device_exists(address):
    return bt_is_connected(address) is not None


def bt_connect(address):
    try:
        path = _dbus_find_bt_device(address)
        if path is None:
            return False

        system = dbus.SystemBus()
        device = dbus.Interface(system.get_object("org.bluez", path),
                                "org.bluez.Device1")
        device.Connect()
        return True
    except dbus.exceptions.DBusException:
        log.exception("Failed to change connection state")
        return False


def bt_disconnect(address):
    try:
        path = _dbus_find_bt_device(address)
        if path is None:
            return False

        system = dbus.SystemBus()
        device = dbus.Interface(system.get_object("org.bluez", path),
                                "org.bluez.Device1")
        device.Disconnect()
        return True
    except dbus.exceptions.DBusException:
        log.exception("Failed to change connection state")
        return False


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

                if props.get("Name", "") == "" and not props.get("Paired", False):
                    continue

                scan_results.append({
                    "name": props.get("Name", ""),
                    "address": props.get("Address", "Unknown address"),
                    "connected": props.get("Connected", False)
                })
    except dbus.exceptions.DBusException:
        log.exception("Failed to list devices")

    return scan_results


def _dbus_find_bt_device(address):
    try:
        system = dbus.SystemBus()
        bluez = dbus.Interface(system.get_object("org.bluez", "/"),
                               "org.freedesktop.DBus.ObjectManager")

        all_objects = bluez.GetManagedObjects()

        for path in all_objects:
            if "org.bluez.Device1" in all_objects[path]:
                device_props = dbus.Interface(system.get_object("org.bluez", path),
                                              "org.freedesktop.DBus.Properties")
                props = _dbus_to_python(device_props.GetAll("org.bluez.Device1"))
                if props.get("Address", "") == address:
                    return path
    except dbus.exceptions.DBusException:
        log.exception("Failed to find device")
        pass

    return None


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
