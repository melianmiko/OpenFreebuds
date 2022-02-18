import logging
import asyncio
import time

# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.bluetooth import BluetoothDevice

from openfreebuds import event_bus
from openfreebuds.manager.base import FreebudsManager

log = logging.getLogger("WindowsFreebudsManager")


async def _async_do_scan():
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


class WindowsFreebudsManager(FreebudsManager):
    def _is_connected(self):
        devices = asyncio.run(_async_do_scan())
        
        for a in devices:
            if a["address"] == self.address:
                return a["connected"]

        return None

    def _device_exists(self):
        return self._is_connected() is not None

    def _do_scan(self):
        self.scan_results = asyncio.run(_async_do_scan())
        time.sleep(3)
        event_bus.invoke(self.EVENT_SCAN_COMPLETE)
