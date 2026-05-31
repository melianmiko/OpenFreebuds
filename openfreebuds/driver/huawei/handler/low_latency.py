import asyncio

from openfreebuds.driver.huawei.constants import CMD_LOW_LATENCY
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiLowLatencyPreferenceHandler(OfbDriverHandlerHuawei):
    """
    Low latency toggle handler
    """

    handler_id = "low_latency"
    commands = [CMD_LOW_LATENCY]

    properties = [
        ("config", "low_latency"),
    ]

    def __init__(self, write_param: int = 1):
        self.write_param = write_param

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_LOW_LATENCY, [2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(2)
        if len(value) == 0:
            return

        await self.driver.put_property("config", "low_latency", "true" if value[0] == 1 else "false")

    async def set_property(self, group: str, prop: str, value: str):
        resp = await self.driver.send_package(HuaweiSppPackage.change_rq(CMD_LOW_LATENCY, [
            (self.write_param, b"\x01" if value == "true" else b"\x00"),
        ]))
        if resp is not None and not resp.is_error_response():
            await self.on_package(resp)
        await asyncio.sleep(1)
        await self.on_init()
