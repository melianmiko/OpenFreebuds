import json
import asyncio

from openfreebuds.driver.huawei.constants import CMD_WEARING_STATUS
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiStateInEarHandler(OfbDriverHandlerHuawei):
    """
    TWS in-ear state detection handler
    """

    handler_id = "tws_in_ear"
    commands = [b'+\x03', CMD_WEARING_STATUS]

    async def on_init(self):
        try:
            resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_WEARING_STATUS, [1, 2, 3, 4]), timeout=2)
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            resp = None

        if resp is not None and not resp.is_error_response():
            await self.on_package(resp)
            return

        await self.driver.put_property("state", "in_ear", "false")

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id == CMD_WEARING_STATUS:
            await self._on_wearing_status(package)
            return

        value = package.find_param(8, 9)
        if len(value) == 1:
            await self.driver.put_property("state", "in_ear", json.dumps(value[0] == 1))

    async def _on_wearing_status(self, package: HuaweiSppPackage):
        left_wearing = self._get_bool_param(package, 1)
        right_wearing = self._get_bool_param(package, 2)
        left_in_box = self._get_bool_param(package, 3)
        right_in_box = self._get_bool_param(package, 4)

        values = {}
        if left_wearing is not None:
            values["in_ear_left"] = json.dumps(left_wearing)
        if right_wearing is not None:
            values["in_ear_right"] = json.dumps(right_wearing)
        if left_in_box is not None:
            values["in_box_left"] = json.dumps(left_in_box)
        if right_in_box is not None:
            values["in_box_right"] = json.dumps(right_in_box)
        if left_wearing is not None or right_wearing is not None:
            values["in_ear"] = json.dumps(bool(left_wearing or right_wearing))

        if values:
            await self.driver.put_property("state", None, values, extend_group=True)

    @staticmethod
    def _get_bool_param(package: HuaweiSppPackage, param_id: int) -> bool | None:
        value = package.find_param(param_id)
        if len(value) != 1:
            return None
        return value[0] == 1
