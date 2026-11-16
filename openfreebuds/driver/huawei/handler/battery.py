import json

from openfreebuds.driver.huawei.constants import CMD_BATTERY_READ, CMD_BATTERY_NOTIFY, CMD_BOX_TONE_INFO
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage

# 0x2B25 response fields (measured 2026-11-13 on FreeClip 2; matches the official App semantics):
#   1 = left earbud worn, 2 = right earbud worn, 3 = left in case, 4 = right in case
# Charging state is not here; it comes from 0x0108 (CMD_BATTERY_READ) param_3: [left, right, case]
_PARAM_LEFT_IN_EAR = 1
_PARAM_RIGHT_IN_EAR = 2
_PARAM_LEFT_IN_BOX = 3
_PARAM_RIGHT_IN_BOX = 4


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
        """0x2B25 is optional; older models that do not respond are skipped after a short wait."""
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

        # The whole battery group is replaced; preserve in-case/worn state read from 0x2B25
        for key in ("in_box", "left_in_box", "right_in_box", "left_in_ear", "right_in_ear"):
            value = await self.driver.get_property("battery", key)
            if value is not None:
                out[key] = value

        await self.driver.put_property("battery", None, out)

    async def _on_in_box(self, package: HuaweiSppPackage):
        left_ear = package.find_param(_PARAM_LEFT_IN_EAR)
        right_ear = package.find_param(_PARAM_RIGHT_IN_EAR)
        left_box = package.find_param(_PARAM_LEFT_IN_BOX)
        right_box = package.find_param(_PARAM_RIGHT_IN_BOX)
        if not any(len(p) for p in (left_ear, right_ear, left_box, right_box)):
            return

        new_props = {}
        if len(left_ear) == 1 and left_ear[0] in (0, 1):
            new_props["left_in_ear"] = json.dumps(left_ear[0] == 1)
        if len(right_ear) == 1 and right_ear[0] in (0, 1):
            new_props["right_in_ear"] = json.dumps(right_ear[0] == 1)
        if len(left_box) == 1 and left_box[0] in (0, 1):
            new_props["left_in_box"] = json.dumps(left_box[0] == 1)
        if len(right_box) == 1 and right_box[0] in (0, 1):
            new_props["right_in_box"] = json.dumps(right_box[0] == 1)

        # Both earbuds must be in the case to count as in-case; this matches the official App
        is_in_box = new_props.get("left_in_box") == "true" and new_props.get("right_in_box") == "true"
        new_props["in_box"] = json.dumps(is_in_box)

        await self.driver.put_property("battery", None, new_props, extend_group=True)
        await self.driver.put_property("state", "headset_in_box", json.dumps(is_in_box))

        # Find-earbud wear protection is per ear; mirror it into the state group here
        for key in ("left_in_ear", "right_in_ear"):
            if key in new_props:
                await self.driver.put_property("state", key, new_props[key])
        if "left_in_ear" in new_props or "right_in_ear" in new_props:
            left = await self.driver.get_property("battery", "left_in_ear")
            right = await self.driver.get_property("battery", "right_in_ear")
            await self.driver.put_property(
                "state", "in_ear", json.dumps(left == "true" or right == "true"))

