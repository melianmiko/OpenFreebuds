import json

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


# Newer models (e.g. FreeBuds Pro 4) push wear state as 2B 25: param 1 and 2 are
# per-earbud flags (1 = in ear). Treat "in ear" as both earbuds worn.
CMD_WEAR_STATE_NOTIFY = b'+\x25'


class OfbHuaweiStateInEarHandler(OfbDriverHandlerHuawei):
    """
    TWS in-ear state detection handler
    """

    handler_id = "tws_in_ear"
    commands = [b'+\x03', CMD_WEAR_STATE_NOTIFY]

    async def on_init(self):
        await self.driver.put_property("state", "in_ear", "false")

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id == CMD_WEAR_STATE_NOTIFY:
            first, second = package.find_param(1), package.find_param(2)
            if len(first) == 1 and len(second) == 1:
                await self.driver.put_property("state", "in_ear", json.dumps(first[0] == 1 and second[0] == 1))
            return

        value = package.find_param(8, 9)
        if len(value) == 1:
            await self.driver.put_property("state", "in_ear", json.dumps(value[0] == 1))
