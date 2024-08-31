import asyncio

from openfreebuds.driver.huawei.constants import CMD_LOW_LATENCY
from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiLowLatencyPreferenceHandler(FbDriverHandlerHuawei):
    """
    Low latency toggle handler
    """

    handler_id = "low_latency"
    commands = [CMD_LOW_LATENCY]

    properties = [
        ("config", "low_latency"),
    ]

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_LOW_LATENCY, [2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(2)
        if len(value) == 0:
            return

        await self.driver.put_property("config", "low_latency", "true" if value[0] == 1 else "false")

    async def set_property(self, group: str, prop: str, value: str):
        await self.driver.send_package(HuaweiSppPackage.change_rq(CMD_LOW_LATENCY, [
            (1, b"\x01" if value == "true" else b"\x00"),
        ]))
        await asyncio.sleep(1)
        await self.on_init()
