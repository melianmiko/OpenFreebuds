import asyncio
import logging

from dbus_next import BusType
from dbus_next.errors import DBusError
from dbus_next.aio import MessageBus, ProxyObject
from dbus_next.introspection import Node

log = logging.getLogger("OfbLinuxBackend")


class DBusConn:
    system: MessageBus = None
    bluez: ProxyObject = None
    bluez_introspect: Node = None

    @staticmethod
    async def prepare():
        if DBusConn.system is None:
            DBusConn.system = await MessageBus(bus_type=BusType.SYSTEM).connect()
            DBusConn.bluez_introspect = await DBusConn.system.introspect("org.bluez", "/")
            DBusConn.bluez = DBusConn.system.get_proxy_object("org.bluez", "/",
                                                              DBusConn.bluez_introspect)


# noinspection PyUnresolvedReferences
async def bt_is_connected(address):
    try:
        device, device_introspect = await _dbus_find_bt_device(address)
        if device is None:
            return None

        interface = device.get_interface("org.bluez.Device1")
        return await interface.get_connected()
    except AttributeError:
        log.exception(f"Failed to check connection state of {address}")
        return False


# noinspection PyUnresolvedReferences
async def bt_connect(address):
    try:
        device, device_introspect = await _dbus_find_bt_device(address)
        if device is None:
            return None

        interface = device.get_interface("org.bluez.Device1")
        await interface.call_connect()
        await asyncio.sleep(1)
        return True
    except DBusError:
        log.exception(f"Failed to change connection state of {address}")
        return False


# noinspection PyUnresolvedReferences
async def bt_disconnect(address):
    try:
        device, device_introspect = await _dbus_find_bt_device(address)
        if device is None:
            return None

        interface = device.get_interface("org.bluez.Device1")
        await interface.call_disconnect()
        await asyncio.sleep(1)
        return True
    except DBusError:
        log.exception(f"Failed to change connection state of {address}")
        return False


# noinspection PyUnresolvedReferences
async def bt_list_devices():
    scan_results = []

    try:
        await DBusConn.prepare()
        obj_manager = DBusConn.bluez.get_interface("org.freedesktop.DBus.ObjectManager")
        # noinspection PyUnresolvedReferences
        all_objects = await obj_manager.call_get_managed_objects()

        for path in all_objects:
            if "org.bluez.Device1" in all_objects[path]:
                device_introspect = await DBusConn.system.introspect("org.bluez", path)
                device = DBusConn.system.get_proxy_object("org.bluez", path, device_introspect)
                properties = device.get_interface("org.freedesktop.DBus.Properties")
                props = await properties.call_get_all("org.bluez.Device1")

                try:
                    scan_results.append({
                        "name": props.get("Name").value,
                        "address": props.get("Address").value,
                        "connected": props.get("Connected").value
                    })
                except AttributeError:
                    log.debug(f"Skip broken bluez device {path}")
    except DBusError:
        log.exception("Failed to list devices")

    return scan_results


# noinspection PyUnresolvedReferences
async def _dbus_find_bt_device(address: str) -> tuple[ProxyObject, Node]:
    try:
        await DBusConn.prepare()
        obj_manager = DBusConn.bluez.get_interface("org.freedesktop.DBus.ObjectManager")
        # noinspection PyUnresolvedReferences
        all_objects = await obj_manager.call_get_managed_objects()

        for path in all_objects:
            if "org.bluez.Device1" in all_objects[path]:
                device_introspect = await DBusConn.system.introspect("org.bluez", path)
                device = DBusConn.system.get_proxy_object("org.bluez", path, device_introspect)
                properties = device.get_interface("org.freedesktop.DBus.Properties")
                addr = await properties.call_get("org.bluez.Device1", "Address")

                try:
                    if addr.value == address:
                        return device, device_introspect
                except AttributeError:
                    pass
    except DBusError:
        log.exception("Failed to find device")
        return None, None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(bt_is_connected("20:18:5B:04:CB:74"))
