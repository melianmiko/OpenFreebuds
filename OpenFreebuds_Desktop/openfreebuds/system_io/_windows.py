import logging
import asyncio

# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.bluetooth import BluetoothDevice
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.networking import HostName

log = logging.getLogger("WindowsFreebudsManager")
HAS_CONNECTION_ACTIONS = False


def is_device_connected(address):
    return asyncio.run(_is_device_connected(address))


async def _is_device_connected(address):
    host_name = HostName(address)
    bt_device = await BluetoothDevice.from_host_name_async(host_name)
    return bt_device.connection_status


def device_exists(address):
    devices = list_paired()

    for a in devices:
        if a["address"] == address:
            return True

    return False


def list_paired():
    return asyncio.run(_list_paired())


async def _list_paired():
    out = []

    try:
        selector = BluetoothDevice.get_device_selector_from_pairing_state(True)
        devices = await DeviceInformation.find_all_async(selector, [], DeviceInformationKind.DEVICE)
        for a in devices:
            bt_device = await BluetoothDevice.from_id_async(a.id)
            out.append({
                "name": bt_device.name,
                "address": bt_device.host_name.raw_name[1:-1],
                "connected": bt_device.connection_status
            })
    except OSError:
        logging.exception("got OSError when listing windows devices")

    return out


def connect_device(address):
    return False


def disconnect_device(address):
    return False
