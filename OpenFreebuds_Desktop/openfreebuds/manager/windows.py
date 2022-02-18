import logging
import asyncio

from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
from winsdk.windows.devices.bluetooth import BluetoothDevice

from openfreebuds.manager.base import FreebudsManager

log = logging.getLogger("WindowsFreebudsManager")


class WindowsFreebudsManager(FreebudsManager):
    def _is_connected(self):
        devices = self._async_do_scan()
        
        for a in self.devices:
            if a["address"] == self.address:
                return a["connected"]

        return None

    def _device_exists(self):
        return self._is_connected() is not None

    def _do_scan(self):
        self.scan_results = asyncio.run(self._async_do_scan())
        self.scan_complete.set()

    async def _async_do_scan(self):
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


if __name__ == "__main__":
    a = WindowsFreebudsManager()
    a._do_scan()
