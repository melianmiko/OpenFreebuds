import logging
import asyncio

# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.bluetooth import BluetoothDevice

log = logging.getLogger("WindowsFreebudsManager")


async def _list_paired():
    out = []

    selector = BluetoothDevice.get_device_selector_from_pairing_state(True)
    devices = await DeviceInformation.find_all_async(selector, [], DeviceInformationKind.DEVICE)
    for a in devices:
        bt_device = await BluetoothDevice.from_id_async(a.id)
        out.append({
            "name": bt_device.name,
            "address": bt_device.host_name.raw_name[1:-1],
            "connected": bt_device.connection_status
        })

    return out


def is_device_connected(address):
    devices = asyncio.run(_list_paired())

    for a in devices:
        if a["address"] == address:
            return a["connected"]

    return None


def device_exists(address):
    return is_device_connected(address) is not None


def list_paired():
    return asyncio.run(_list_paired())
