import json

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiAdaptiveVolumeHandler")

# 0x2BB4 载荷字段（真机 FreeClip 2 实测）：
#   1 = featureId（回显 0x02）
#   2 = 能力位（1 = 支持）
#   3 = 开关状态（0 = 关，1 = 开）
#   4 = 灵敏度（0 = low，1 = default，2 = high），旧固件可能不存在
_PARAM_FEATURE = 1
_PARAM_SUPPORT = 2
_PARAM_STATE = 3
_PARAM_LEVEL = 4

LEVEL_NAMES = {
    0: "low",
    1: "default",
    2: "high",
}
LEVEL_VALUES = {name: value for value, name in LEVEL_NAMES.items()}


def _build_read_rq():
    """
    构造 0x2BB4 读请求：01 01 02 02 00 03 00 04 00
    """
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME),
        (_PARAM_SUPPORT, b""),
        (_PARAM_STATE, b""),
        (_PARAM_LEVEL, b""),
    ])


def _build_write_rq(enabled: bool):
    """
    构造 0x2BB4 写请求：01 01 02 03 01 <0/1>
    """
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME),
        (_PARAM_STATE, 1 if enabled else 0),
    ])


def _build_level_rq(level: int):
    """
    构造 0x2BB4 写灵敏度请求：01 01 02 04 01 <0/1/2>
    """
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME),
        (_PARAM_LEVEL, level),
    ])


class OfbHuaweiAdaptiveVolumeHandler(OfbDriverHandlerHuawei):
    """
    自适应音量 handler（0x2BB4 MBB 通道，featureId 2）

    目前确认 FreeClip 2 支持；其他机型无响应时属性保持 unsupported。
    灵敏度（p4）按字段存在性启用，旧固件不下发 level 属性。
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
        self.level_supported: bool = False

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

        support = package.find_param(_PARAM_SUPPORT)
        if len(support) == 1:
            self.supported = support[0] == 1
            new_props["adaptive_volume_supported"] = json.dumps(self.supported)

        state = package.find_param(_PARAM_STATE)
        if len(state) == 1:
            new_props["adaptive_volume"] = json.dumps(state[0] != 0)

        level = package.find_param(_PARAM_LEVEL)
        if len(level) == 1 and level[0] in LEVEL_NAMES:
            level_name = LEVEL_NAMES[level[0]]
        else:
            # Level is optional on older firmware, keep the control available.
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
