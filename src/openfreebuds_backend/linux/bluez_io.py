import asyncio
import logging

from sdbus import sd_bus_open_system, SdBusBaseError

from openfreebuds.utils.logger import create_logger
from openfreebuds_backend.linux.dbus import BluezDevice1Proxy, BluezProxy

log = create_logger("LinuxBackend")
system_bus = sd_bus_open_system()


async def bt_is_connected(address):
    try:
        path = await _dbus_find_bt_device(address)
        if path is None:
            return None

        proxy = BluezDevice1Proxy.new_proxy("org.bluez",
                                            object_path=path,
                                            bus=system_bus)
        return await proxy.Connected
    except SdBusBaseError:
        log.exception(f"Failed to check connection state of {address}")
        return False


def bt_device_exists(address):
    return bt_is_connected(address) is not None


async def bt_connect(address):
    try:
        path = await _dbus_find_bt_device(address)
        if path is None:
            return None

        proxy = BluezDevice1Proxy.new_proxy("org.bluez",
                                            object_path=path,
                                            bus=system_bus)
        await proxy.Connect()
        await asyncio.sleep(1)
        return True
    except SdBusBaseError:
        log.exception(f"Failed to change connection state of {address}")
        return False


async def bt_disconnect(address):
    try:
        path = await _dbus_find_bt_device(address)
        if path is None:
            return None

        proxy = BluezDevice1Proxy.new_proxy("org.bluez",
                                            object_path=path,
                                            bus=system_bus)
        await proxy.Disconnect()
        await asyncio.sleep(1)
        return True
    except SdBusBaseError:
        log.exception(f"Failed to change connection state of {address}")
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


async def _dbus_find_bt_device(address):
    proxy = BluezProxy.new_proxy("org.bluez",
                                 object_path="/",
                                 bus=system_bus)
    all_objects = await proxy.get_managed_objects()

    for path in all_objects:
        if "org.bluez.Device1" in all_objects[path]:
            _, addr = all_objects[path]["org.bluez.Device1"]["Address"]
            if addr == address:
                return path

    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(bt_is_connected("DC:D4:44:28:6F:AE"))
