import asyncio
from contextlib import suppress

import openfreebuds_backend
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict
from openfreebuds.utils.logger import create_logger


log = create_logger("OfnHuaweiSoundQualityPreferenceHandler")


class OfnHuaweiSoundQualityPreferenceHandler(OfbDriverHandlerHuawei):
    """
    Sound quality preference option from 5i, and maybe other devices too
    """
    handler_id = "config_sound_quality"
    commands = [b"\x2b\xa3"]
    ignore_commands = [b"\x2b\xa2"]
    properties = [
        ("sound", "quality_preference"),
    ]

    def __init__(self):
        super().__init__()
        self._codec_reconnect_task: asyncio.Task | None = None
        self.options = {
            0: "sqp_connectivity",
            1: "sqp_quality",
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\xa3", [1]))
        await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
        value = reverse_dict(self.options)[value]
        pkg = HuaweiSppPackage.change_rq(b"\x2b\xa2", [
            (1, value),
        ])

        try:
            await self.driver.send_package(pkg)
        finally:
            self._schedule_codec_reconnect()
        await self.on_init()

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(2)

        if len(value) == 1:
            value = int.from_bytes(value, byteorder="big", signed=True)
            await self.driver.put_property("sound", "quality_preference",
                                           self.options[value])
            await self.driver.put_property("sound", "quality_preference_options",
                                           ",".join(self.options.values()))

    def _schedule_codec_reconnect(self):
        if self._codec_reconnect_task is not None and not self._codec_reconnect_task.done():
            self._codec_reconnect_task.cancel()
        self._codec_reconnect_task = asyncio.create_task(self._reconnect_after_codec_switch())

    async def _reconnect_after_codec_switch(self):
        with suppress(asyncio.CancelledError):
            await asyncio.sleep(3)
            for _ in range(3):
                try:
                    if await openfreebuds_backend.bt_is_connected(self.driver.device_address):
                        return

                    log.info("Trying Bluetooth reconnect after codec switch")
                    await openfreebuds_backend.bt_connect(self.driver.device_address)
                except Exception:
                    log.exception("Bluetooth reconnect after codec switch failed")
                await asyncio.sleep(3)
