import json

from openfreebuds.driver.huawei.constants import CMD_AUTO_PAUSE_READ, CMD_AUTO_PAUSE_WRITE
from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class FbHuaweiConfigAutoPauseHandler(FbDriverHandlerHuawei):
    """
    TWS pause when plug off config handler
    """

    handler_id = "tws_auto_pause"
    commands = [CMD_AUTO_PAUSE_READ, CMD_AUTO_PAUSE_WRITE]
    properties = [
        ("config", "auto_pause"),
    ]

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_AUTO_PAUSE_READ, [1]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        data = package.find_param(1)
        if len(data) == 1:
            await self.driver.put_property("config", "auto_pause", json.dumps(data[0] == 1))

    async def set_property(self, group: str, prop: str, value):
        resp = await self.driver.send_package(HuaweiSppPackage.change_rq(CMD_AUTO_PAUSE_WRITE, [
            (1, 1 if value == "true" else 0)
        ]))
        if resp.find_param(127) is not None:
            await self.driver.put_property(group, prop, value)
