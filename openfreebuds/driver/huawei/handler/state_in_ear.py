import json

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage

CMD_TWS_WEAR_STATE = b"\x2b\x25"


class OfbHuaweiStateInEarHandler(OfbDriverHandlerHuawei):
    """
    TWS in-ear state detection handler
    """

    handler_id = "tws_in_ear"
    commands = [b'+\x03']

    def __init__(self, w_wear_state: bool = False):
        """
        @param w_wear_state: Device reports per-earbud wear state via 2b25 (tested on 7i)
        """
        self.w_wear_state = w_wear_state
        if w_wear_state:
            self.commands = [b'+\x03', CMD_TWS_WEAR_STATE]

    async def on_init(self):
        await self.driver.put_property("state", "in_ear", "false")
        if self.w_wear_state:
            resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_TWS_WEAR_STATE, [1, 2]))
            await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id == CMD_TWS_WEAR_STATE:
            # 1 = left, 2 = right; in ear only when both earbuds are worn
            left, right = package.find_param(1), package.find_param(2)
            if len(left) == 1 and len(right) == 1:
                await self.driver.put_property("state", "in_ear", json.dumps(left[0] == 1 and right[0] == 1))
            return

        value = package.find_param(8, 9)
        if len(value) == 1:
            await self.driver.put_property("state", "in_ear", json.dumps(value[0] == 1))
