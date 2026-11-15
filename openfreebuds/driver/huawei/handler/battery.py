import json

from openfreebuds.driver.huawei.constants import CMD_BATTERY_READ, CMD_BATTERY_NOTIFY, CMD_BOX_TONE_INFO
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage

# 0x2B25 响应字段（真机 FreeClip 2 实测）：
#   1 = 左耳佩戴，2 = 右耳佩戴，3 = 充电中，4 = 在盒
_PARAM_CHARGING = 3
_PARAM_IN_BOX = 4


class OfbHuaweiBatteryHandler(OfbDriverHandlerHuawei):
    """
    Battery read handler
    """

    handler_id = "battery"
    commands = [CMD_BATTERY_READ, CMD_BATTERY_NOTIFY, CMD_BOX_TONE_INFO]

    def __init__(self, w_tws: bool = True):
        self.w_tws = w_tws

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_BATTERY_READ, [1, 2, 3]))
        await self.on_package(resp)
        await self._read_in_box()

    async def _read_in_box(self):
        """
        0x2B25 为可选能力，旧机型无响应时短暂等待后静默跳过
        """
        try:
            resp = await self.driver.send_package(
                HuaweiSppPackage.read_rq(CMD_BOX_TONE_INFO, [1, 2, 3, 4]),
                timeout=1,
            )
        except TimeoutError:
            return

        if resp is not None:
            await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None:
            return

        if package.command_id == CMD_BOX_TONE_INFO:
            await self._on_in_box(package)
            return

        out = {}
        if 1 in package.parameters and len(package.parameters[1]) == 1:
            out["global"] = int(package.parameters[1][0])
        if 2 in package.parameters and len(package.parameters[2]) == 3 and self.w_tws:
            level = package.parameters[2]
            out["left"] = int(level[0])
            out["right"] = int(level[1])
            out["case"] = int(level[2])
        if 3 in package.parameters and len(package.parameters[3]) > 0:
            charging = package.parameters[3]
            if len(charging) == 3:
                out["left_charging"] = json.dumps(charging[0] == 1)
                out["right_charging"] = json.dumps(charging[1] == 1)
                out["case_charging"] = json.dumps(charging[2] == 1)
            out["is_charging"] = json.dumps(b"\x01" in charging)

        # 整个 battery 组会被覆盖，保留由 0x2B25 读到的在盒状态
        for key in ("in_box", "left_in_box", "right_in_box"):
            value = await self.driver.get_property("battery", key)
            if value is not None:
                out[key] = value

        await self.driver.put_property("battery", None, out)

    async def _on_in_box(self, package: HuaweiSppPackage):
        left = package.find_param(1)
        right = package.find_param(2)
        charging = package.find_param(_PARAM_CHARGING)
        in_box = package.find_param(_PARAM_IN_BOX)
        if len(left) == 0 and len(right) == 0 and len(charging) == 0 and len(in_box) == 0:
            return

        new_props = {}
        if len(left) == 1 and left[0] in (0, 1):
            new_props["left_in_box"] = json.dumps(left[0] == 1)
        if len(right) == 1 and right[0] in (0, 1):
            new_props["right_in_box"] = json.dumps(right[0] == 1)

        if len(in_box) == 1:
            is_in_box = in_box[0] == 1
        else:
            is_in_box = new_props.get("left_in_box") == "true" and new_props.get("right_in_box") == "true"
        new_props["in_box"] = json.dumps(is_in_box)

        await self.driver.put_property("battery", None, new_props, extend_group=True)
        await self.driver.put_property("state", "headset_in_box", json.dumps(is_in_box))

