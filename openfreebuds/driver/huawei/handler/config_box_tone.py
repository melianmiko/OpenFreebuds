import json

from openfreebuds.driver.huawei.constants import (
    CMD_BOX_TONE,
    CMD_BOX_TONE_INFO,
    CMD_MBB_FEATURE,
    MBB_FEATURE_BOX_TONE,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.driver.huawei.utils import crc16_xmodem
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiBoxToneHandler")

# 0x2BB1 响应字段：2 = 是否支持，3 = 开关状态
_PARAM_SUPPORT = 2
_PARAM_STATE = 3

# 0x2B25 响应字段（真机 FreeClip 2 实测）：
#   1 = 左耳佩戴，2 = 右耳佩戴，3 = 充电中，4 = 在盒
_PARAM_CHARGING = 3
_PARAM_IN_BOX = 4

# 0x2BB4 MBB feature 16 (BOX_TONE) 字段：
#   1 = featureId，2 = 能力位，3 = 总开关
#   4 = 开盖提示音开关，5 = 开盖提示音音量（0-100）
#   p4/p5 旧固件可能不存在
_MBB_PARAM_FEATURE = 1
_MBB_PARAM_SUPPORT = 2
_MBB_PARAM_STATE = 3
_MBB_PARAM_LID_ENABLED = 4
_MBB_PARAM_LID_VOLUME = 5

_MBB_READ_TIMEOUT = 0.5


def _build_tone_state_rq():
    """
    构造 0x2BB1 查询：02 00 03 00
    """
    return HuaweiSppPackage.read_rq(CMD_BOX_TONE, [_PARAM_SUPPORT, _PARAM_STATE])


def _build_tone_info_rq():
    """
    构造 0x2B25 查询：03 00
    """
    return HuaweiSppPackage.read_rq(CMD_BOX_TONE_INFO, [3])


def _build_mbb_read_rq():
    """
    构造 0x2BB4 BOX_TONE 查询：01 01 10 02 00 03 00 04 00 05 00
    """
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_MBB_PARAM_FEATURE, MBB_FEATURE_BOX_TONE),
        (_MBB_PARAM_SUPPORT, b""),
        (_MBB_PARAM_STATE, b""),
        (_MBB_PARAM_LID_ENABLED, b""),
        (_MBB_PARAM_LID_VOLUME, b""),
    ])


def _build_lid_enabled_rq(enabled: bool):
    """
    构造 0x2BB4 写开盖提示音开关：01 01 10 04 01 <0/1>
    """
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_MBB_PARAM_FEATURE, MBB_FEATURE_BOX_TONE),
        (_MBB_PARAM_LID_ENABLED, 1 if enabled else 0),
    ])


def _build_lid_volume_rq(volume: int):
    """
    构造 0x2BB4 写开盖提示音音量：01 01 10 05 01 <0..100>
    """
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_MBB_PARAM_FEATURE, MBB_FEATURE_BOX_TONE),
        (_MBB_PARAM_LID_VOLUME, volume),
    ])


def _build_tone_write_payload(enabled: bool) -> bytes:
    """
    0x2BB1 写入载荷固定为 `00 00 <0/1>`（非 TLV 结构）
    """
    return b"\x00\x00" + (b"\x01" if enabled else b"\x00")


class _RawPayloadPackage(HuaweiSppPackage):
    """
    0x2BB1 写入载荷 `00 00 <0/1>` 不是 TLV，无法用 parameters 表达，
    这里保留原始载荷，帧头与校验算法与华为 SPP 保持一致。
    """

    def __init__(self, cmd: bytes, payload: bytes):
        super().__init__(cmd=cmd, resp=cmd)
        self.raw_payload = payload

    def to_bytes(self):
        body = self.command_id + self.raw_payload
        result = b"Z" + (len(body) + 1).to_bytes(2, byteorder="big") + b"\x00" + body
        return result + crc16_xmodem(result)


class OfbHuaweiBoxToneHandler(OfbDriverHandlerHuawei):
    """
    充电盒提示音 handler（0x2BB1 总开关，0x2B25 能力/在盒状态，0x2BB4 feature 16 开盖提示音）
    """

    handler_id = "config_box_tone"
    commands = [CMD_BOX_TONE, CMD_BOX_TONE_INFO, CMD_MBB_FEATURE]
    # 协议尚未在真机标定，缩短初始化重试，避免旧固件无响应时阻塞连接
    init_timeout = 1
    init_attempt_max = 2
    properties = [
        ("config", "box_tone_enabled"),
        ("config", "box_tone_supported"),
        ("config", "box_tone_lid_enabled"),
        ("config", "box_tone_lid_volume"),
        ("config", "box_tone_lid_supported"),
        ("state", "headset_in_box"),
    ]

    async def on_init(self):
        resp = await self.driver.send_package(_build_tone_state_rq())
        if resp is not None:
            await self.on_package(resp)

        resp = await self.driver.send_package(_build_tone_info_rq())
        if resp is not None:
            await self.on_package(resp)

        try:
            # 旧固件没有 feature 16，短超时后直接保持 0x2BB1 的原有行为
            resp = await self.driver.send_package(_build_mbb_read_rq(), timeout=_MBB_READ_TIMEOUT)
        except TimeoutError:
            log.info("No MBB box tone response, skipping lid tone controls")
            return

        if resp is not None:
            await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None:
            return

        if package.command_id == CMD_BOX_TONE:
            await self._on_tone_state(package)
        elif package.command_id == CMD_BOX_TONE_INFO:
            await self._on_tone_info(package)
        elif package.command_id == CMD_MBB_FEATURE:
            await self._on_mbb_feature(package)

    async def _on_tone_state(self, package: HuaweiSppPackage):
        new_props = {}

        support = package.find_param(_PARAM_SUPPORT)
        if len(support) >= 1:
            new_props["box_tone_supported"] = json.dumps(support[0] == 1)

        state = package.find_param(_PARAM_STATE)
        if len(state) >= 1:
            new_props["box_tone_enabled"] = json.dumps(state[0] == 1)

        if new_props.get("box_tone_supported") == "true":
            # Feature 16 may not answer on this firmware; expose the lid
            # controls anyway, using neutral defaults until device reports.
            new_props["box_tone_lid_supported"] = "true"
            if await self.driver.get_property("config", "box_tone_lid_enabled") is None:
                new_props["box_tone_lid_enabled"] = "false"
            if await self.driver.get_property("config", "box_tone_lid_volume") is None:
                new_props["box_tone_lid_volume"] = "50"

        if len(new_props) > 0:
            await self.driver.put_property("config", None, new_props, extend_group=True)

    async def _on_tone_info(self, package: HuaweiSppPackage):
        """
        0x2B25 返回左右耳在盒、充电与整体在盒状态，用于推导 headset_in_box。
        """
        left = package.find_param(1)
        right = package.find_param(2)
        charging = package.find_param(_PARAM_CHARGING)
        in_box = package.find_param(_PARAM_IN_BOX)
        if len(left) == 0 and len(right) == 0 and len(charging) == 0 and len(in_box) == 0:
            return

        if len(in_box) == 1:
            is_in_box = in_box[0] == 1
        elif len(left) == 1 and len(right) == 1:
            is_in_box = left[0] == 1 and right[0] == 1
        else:
            is_in_box = len(charging) == 1 and charging[0] == 1

        await self.driver.put_property("state", "headset_in_box", json.dumps(is_in_box))

    async def _on_mbb_feature(self, package: HuaweiSppPackage):
        """
        解析 feature 16 (BOX_TONE)：设备有响应即视为支持开盖提示音，
        p4/p5 缺失时使用缺省值，保证控件可用。
        """
        feature = package.find_param(_MBB_PARAM_FEATURE)
        if len(feature) == 0 or feature[0] != MBB_FEATURE_BOX_TONE:
            return

        new_props = {}

        # Device answered on feature 16, so expose lid controls even if the
        # optional p4/p5 fields are missing on this firmware.
        new_props["box_tone_lid_supported"] = "true"

        state = package.find_param(_MBB_PARAM_STATE)
        if len(state) == 1:
            new_props["box_tone_enabled"] = json.dumps(state[0] != 0)

        lid_enabled = package.find_param(_MBB_PARAM_LID_ENABLED)
        if len(lid_enabled) == 1:
            new_props["box_tone_lid_enabled"] = json.dumps(lid_enabled[0] != 0)
        else:
            new_props["box_tone_lid_enabled"] = "false"

        lid_volume = package.find_param(_MBB_PARAM_LID_VOLUME)
        if len(lid_volume) == 1 and 0 <= lid_volume[0] <= 100:
            new_props["box_tone_lid_volume"] = str(lid_volume[0])
        else:
            new_props["box_tone_lid_volume"] = "50"

        if len(new_props) > 0:
            await self.driver.put_property("config", None, new_props, extend_group=True)

    async def set_property(self, group: str, prop: str, value: str):
        if prop not in ("box_tone_enabled", "box_tone_lid_enabled", "box_tone_lid_volume"):
            log.warning(f"Property {group}//{prop} is read-only, ignoring write")
            return False

        if await self.driver.get_property("state", "headset_in_box") != "true":
            log.warning(f"Headset isn't in the charging case, ignoring write {group}//{prop}")
            return False

        if prop == "box_tone_enabled":
            if await self.driver.get_property("config", "box_tone_supported") == "false":
                log.warning("Device doesn't support box tone, ignoring write")
                return False

            pkg = _RawPayloadPackage(CMD_BOX_TONE, _build_tone_write_payload(value == "true"))
            resp = await self.driver.send_package(pkg)
            if resp is not None:
                await self.on_package(resp)
            return True

        if await self.driver.get_property("config", "box_tone_lid_supported") != "true":
            log.warning("Device doesn't support lid tone, ignoring write")
            return False

        if prop == "box_tone_lid_enabled":
            pkg = _build_lid_enabled_rq(value == "true")
        else:
            try:
                volume = int(value)
            except (TypeError, ValueError):
                log.warning(f"Invalid lid tone volume {value}, ignoring write")
                return False
            if not 0 <= volume <= 100:
                log.warning(f"Lid tone volume {volume} is out of range, ignoring write")
                return False
            pkg = _build_lid_volume_rq(volume)

        resp = await self.driver.send_package(pkg)
        if resp is not None:
            await self.on_package(resp)
        return True
