from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class FbHuaweiStateInEarHandler(FbDriverHandlerHuawei):
    """
    TWS in-ear state detection handler
    """

    handler_id = "tws_in_ear"
    commands = [b'+\x03']

    async def on_init(self):
        await self.driver.put_property("state", "in_ear", "false")

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(8, 9)
        if len(value) == 1:
            await self.driver.put_property("state", "in_ear", value[0] == 1)
