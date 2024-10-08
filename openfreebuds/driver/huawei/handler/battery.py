import json

from openfreebuds.driver.huawei.constants import CMD_BATTERY_READ, CMD_BATTERY_NOTIFY
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiBatteryHandler(OfbDriverHandlerHuawei):
    """
    Battery read handler
    """

    handler_id = "battery"
    commands = [CMD_BATTERY_READ, CMD_BATTERY_NOTIFY]

    def __init__(self, w_tws: bool = True):
        self.w_tws = w_tws

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_BATTERY_READ, [1, 2, 3]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        out = {}
        if 1 in package.parameters and len(package.parameters[1]) == 1:
            out["global"] = int(package.parameters[1][0])
        if 2 in package.parameters and len(package.parameters[2]) == 3 and self.w_tws:
            level = package.parameters[2]
            out["left"] = int(level[0])
            out["right"] = int(level[1])
            out["case"] = int(level[2])
        if 3 in package.parameters and len(package.parameters[3]) > 0:
            out["is_charging"] = json.dumps(b"\x01" in package.parameters[3])
        await self.driver.put_property("battery", None, out)
