import json

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiStateInEarHandler(OfbDriverHandlerHuawei):
    """
    TWS in-ear state detection handler
    """

    handler_id = "tws_in_ear"
    commands = [b'+\x03', b'+\x25']

    async def on_init(self):
        await self.driver.put_property("state", "in_ear", "false")

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id == b'+\x25':
            first = package.find_param(1)
            second = package.find_param(2)
            if len(first) == len(second) == 1:
                await self.driver.put_property("state", "in_ear", json.dumps(first[0] == 1 and second[0] == 1))
            return

        value = package.find_param(8, 9)
        if len(value) == 1:
            await self.driver.put_property("state", "in_ear", json.dumps(value[0] == 1))
