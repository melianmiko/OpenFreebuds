import asyncio
from typing import Optional

from openfreebuds import IOpenFreebuds, is_device_supported
from openfreebuds.utils.logger import create_logger
from openfreebuds_backend import bt_list_devices
from openfreebuds_qt.config.main import OfbQtConfigParser

log = create_logger("OfbQtDeviceAutoSelect")


class OfbQtDeviceAutoSelect:
    def __init__(self, ofb: IOpenFreebuds):
        self.ofb = ofb
        self._task: Optional[asyncio.Task] = None

    async def boot(self):
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._mainloop())

    async def close(self):
        self._task.cancel()
        await self._task
        self._task = None

    async def _mainloop(self):
        log.info("AutoSetup handler started")

        while True:
            try:
                state = await self.ofb.get_state()
                if state not in [IOpenFreebuds.STATE_CONNECTED, IOpenFreebuds.STATE_WAIT]:
                    await OfbQtDeviceAutoSelect.trigger(self.ofb)
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break

        log.info("AutoSetup handler exited")

    @staticmethod
    async def trigger(ofb: IOpenFreebuds):
        enabled = OfbQtConfigParser.get_instance().get("device", "auto_setup", True)
        if not enabled or ofb.role != "standalone":
            return

        state = await ofb.get_state()
        if state in [IOpenFreebuds.STATE_CONNECTED, IOpenFreebuds.STATE_WAIT]:
            return

        paired_devices = await bt_list_devices()
        _, current_addr = await ofb.get_device_tags()

        for bt_dev in paired_devices:
            if not bt_dev["connected"]:
                continue

            name = bt_dev["name"]
            address = bt_dev["address"]
            if is_device_supported(name) and address != current_addr:
                log.info(f"Automatically switch to device name={name}, address={address}")

                config = OfbQtConfigParser.get_instance()
                if config.get("device", "address", "") != address:
                    config.set_device_data(name, address)
                    config.save()

                await ofb.start(name, address)
                break
