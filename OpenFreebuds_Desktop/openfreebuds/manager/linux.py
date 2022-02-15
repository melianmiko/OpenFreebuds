import dbus
from dbus.mainloop.glib import DBusGMainLoop

from openfreebuds.manager.base import FreebudsManager

DBusGMainLoop(set_as_default=True)


class LinuxFreebudsManager(FreebudsManager):
    def _is_connected(self):
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
                    if props.get("Address", "") == self.address:
                        return props.get("Connected", False)
        except dbus.exceptions.DBusException:
            pass

        return None

    def _device_exists(self):
        return self._is_connected() is not None

    def _do_scan(self):
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
                    self.scan_results.append({
                        "name": props.get("Name", ""),
                        "address": props.get("Address", "Unknown address"),
                        "connected": props.get("Connected", False)
                    })
        except dbus.exceptions.DBusException:
            print("WARN: Scan failed due to dbus error")

        self.scan_complete.set()


# From https://stackoverflow.com/questions/11486443/dbus-python-how-to-get-response-with-native-types
def dbus_to_python(data):
    import dbus

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
