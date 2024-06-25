from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class FbHuaweiConfigAutoPauseHandler(FbDriverHandlerHuawei):
    """
    TWS pause when plug off config handler
    """

    handler_id = "tws_auto_pause"
    commands = [b'\x2b\x11', b'\x2b\x10']
    properties = [
        ("config", "auto_pause"),
    ]

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\x11", [1]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        data = package.find_param(1)
        if len(data) == 1:
            await self.driver.put_property("config", "auto_pause", data[0] == 1)

    async def set_property(self, group: str, prop: str, value):
        resp = await self.driver.send_package(HuaweiSppPackage.change_rq(b"\x2b\x10", [
            (1, 1 if value else 0)
        ]))
        if resp.find_param(2)[0] == 0:
            await self.driver.put_property(group, prop, value)
