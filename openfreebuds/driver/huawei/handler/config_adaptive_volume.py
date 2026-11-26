import json

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiAdaptiveVolumeHandler")

# 0x2BB4 payload fields (measured 2026-11-13 on FreeClip 2):
#   1 = featureId (echoes 0x02)
#   2 = switch (0 = off, 1 = on); presence of the field means supported
#   3 = sensitivity (0 = low, 1 = default, 2 = high)
_PARAM_FEATURE = 1
_PARAM_STATE = 2
_PARAM_LEVEL = 3

LEVEL_NAMES = {
    0: "low",
    1: "default",
    2: "high",
}
LEVEL_VALUES = {name: value for value, name in LEVEL_NAMES.items()}


def _build_read_rq():
    """Build the 0x2BB4 read request: 01 01 02 02 00 03 00"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME),
        (_PARAM_STATE, b""),
        (_PARAM_LEVEL, b""),
    ])


def _build_write_rq(enabled: bool):
    """Build the 0x2BB4 switch write: 01 01 02 02 01 <0/1>"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME),
        (_PARAM_STATE, 1 if enabled else 0),
    ])


def _build_level_rq(level: int):
    """Build the 0x2BB4 sensitivity write: 01 01 02 03 01 <0/1/2>"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME),
        (_PARAM_LEVEL, level),
    ])


class OfbHuaweiAdaptiveVolumeHandler(OfbDriverHandlerHuawei):
    """Adaptive volume handler (0x2BB4 MBB, featureId 2).
    Confirmed on FreeClip 2; other models leave the property unsupported when they do not respond.
    """

    handler_id = "config_adaptive_volume"
    commands = [CMD_MBB_FEATURE]
    init_timeout = 1
    init_attempt_max = 2
    properties = [
        ("sound", "adaptive_volume"),
        ("sound", "adaptive_volume_supported"),
        ("sound", "adaptive_volume_level"),
        ("sound", "adaptive_volume_level_options"),
    ]

    def __init__(self):
        self.supported: bool = False

    async def on_init(self):
        resp = await self.driver.send_package(_build_read_rq())
        if resp is None:
            await self.driver.put_property("sound", "adaptive_volume_supported", "false")
            return

        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None or package.command_id != CMD_MBB_FEATURE:
            return

        feature = package.find_param(_PARAM_FEATURE)
        if len(feature) == 0 or feature[0] != MBB_FEATURE_ADAPTIVE_VOLUME:
            return

        new_props = {}

        state = package.find_param(_PARAM_STATE)
        if len(state) == 1:
            self.supported = True
            new_props["adaptive_volume_supported"] = "true"
            new_props["adaptive_volume"] = json.dumps(state[0] != 0)
        else:
            # Feature echo only, no switch field -> unsupported
            self.supported = False
            new_props["adaptive_volume_supported"] = "false"

        level = package.find_param(_PARAM_LEVEL)
        if len(level) == 1 and level[0] in LEVEL_NAMES:
            level_name = LEVEL_NAMES[level[0]]
        else:
            level_name = "default"
        new_props["adaptive_volume_level"] = level_name
        new_props["adaptive_volume_level_options"] = ",".join(LEVEL_VALUES)

        if len(new_props) > 0:
            await self.driver.put_property("sound", None, new_props, extend_group=True)

    async def set_property(self, group: str, prop: str, value: str):
        if prop == "adaptive_volume":
            if not self.supported:
                log.warning("Device doesn't support adaptive volume, ignoring write")
                return False

            resp = await self.driver.send_package(_build_write_rq(value == "true"))
            if resp is not None:
                await self.on_package(resp)
            return True

        if prop == "adaptive_volume_level":
            if not self.supported:
                log.warning("Device doesn't support adaptive volume level, ignoring write")
                return False

            if await self.driver.get_property("sound", "adaptive_volume") != "true":
                log.warning("Adaptive volume is disabled, ignoring level write")
                return False

            if value not in LEVEL_VALUES:
                log.warning(f"Unknown adaptive volume level {value}, ignoring write")
                return False

            resp = await self.driver.send_package(_build_level_rq(LEVEL_VALUES[value]))
            if resp is not None:
                await self.on_package(resp)
            return True

        log.warning(f"Property {group}//{prop} is read-only, ignoring write")
        return False