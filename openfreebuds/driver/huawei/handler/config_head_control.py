import json

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_HEAD_CONTROL
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiHeadControlHandler")

# 0x2BB4 payload fields (measured on FreeClip 2):
#   1 = featureId (echoes 0x0b)
#   2 = switch state (0 = off, 1 = on)
#   3 = nod action (0 none, 1 answer, 2 reject)
#   4 = shake action (0 none, 1 answer, 2 reject)
_PARAM_FEATURE = 1
_PARAM_ENABLED = 2
_PARAM_NOD_ACTION = 3
_PARAM_SHAKE_ACTION = 4

ACTION_NAMES = {
    0: "none",
    1: "answer",
    2: "reject",
}
ACTION_VALUES = {name: value for value, name in ACTION_NAMES.items()}


def _build_read_rq():
    """Build the 0x2BB4 read request: 01 01 0b"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_HEAD_CONTROL),
    ])


def _build_write_rq(param: int, value: int):
    """Build the 0x2BB4 write request: 01 01 0b <param> 01 <value>"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_HEAD_CONTROL),
        (param, value),
    ])


class OfbHuaweiHeadControlHandler(OfbDriverHandlerHuawei):
    """Head-control handler for nod/shake call actions (0x2BB4 MBB).
    Head gestures are reported over the Bluetooth call channel; SPP only carries the switch and action mapping.
    """

    handler_id = "config_head_control"
    commands = [CMD_MBB_FEATURE]
    init_timeout = 1
    init_attempt_max = 2
    properties = [
        ("config", "head_control_enabled"),
        ("config", "head_control_nod_action"),
        ("config", "head_control_shake_action"),
        ("config", "head_control_supported"),
    ]

    def __init__(self):
        self.supported: bool = False

    async def on_init(self):
        resp = await self.driver.send_package(_build_read_rq())
        if resp is None:
            await self.driver.put_property("config", "head_control_supported", "false")
            return

        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None or package.command_id != CMD_MBB_FEATURE:
            return

        feature = package.find_param(_PARAM_FEATURE)
        if len(feature) == 0 or feature[0] != MBB_FEATURE_HEAD_CONTROL:
            return

        self.supported = True
        new_props = {
            "head_control_supported": "true",
        }

        enabled = package.find_param(_PARAM_ENABLED)
        if len(enabled) == 1:
            new_props["head_control_enabled"] = json.dumps(enabled[0] == 1)

        nod_action = package.find_param(_PARAM_NOD_ACTION)
        if len(nod_action) == 1 and nod_action[0] in ACTION_NAMES:
            new_props["head_control_nod_action"] = ACTION_NAMES[nod_action[0]]

        shake_action = package.find_param(_PARAM_SHAKE_ACTION)
        if len(shake_action) == 1 and shake_action[0] in ACTION_NAMES:
            new_props["head_control_shake_action"] = ACTION_NAMES[shake_action[0]]

        await self.driver.put_property("config", None, new_props, extend_group=True)

    async def set_property(self, group: str, prop: str, value: str):
        if not self.supported:
            log.warning(f"Device doesn't support head control, ignoring write {group}//{prop}")
            return False

        if prop == "head_control_enabled":
            return await self._send(_build_write_rq(_PARAM_ENABLED, 1 if value == "true" else 0))

        if prop in ("head_control_nod_action", "head_control_shake_action"):
            if value not in ACTION_VALUES:
                log.warning(f"Unknown head control action {value}, ignoring write")
                return False
            param = _PARAM_NOD_ACTION if prop == "head_control_nod_action" else _PARAM_SHAKE_ACTION
            return await self._send(_build_write_rq(param, ACTION_VALUES[value]))

        log.warning(f"Property {group}//{prop} is read-only, ignoring write")
        return False

    async def _send(self, package: HuaweiSppPackage) -> bool:
        resp = await self.driver.send_package(package)
        if resp is not None:
            await self.on_package(resp)
        return True
