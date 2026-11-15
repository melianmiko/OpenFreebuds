"""充电盒提示音 handler 测试（0x2BB1 总开关 / 0x2B25 在盒 / 0x2BB4 feature 16 开盖提示音）

协议依据 2026-11-13 FreeClip 2 真机标定：
  0x2BB1 读：02 00 03 00 → p2=开关 p3=支持；写：01 01 <0/1>
  0x2B25：p1=左耳佩戴 p2=右耳佩戴 p3=左耳在盒 p4=右耳在盒
  feature 16：p2=12 字节 payload，b0=总开关 b1=开盖开关 b2=音量（0-15）；
              单字节写无效，必须整包写 p2（01 01 10 02 0c <payload>）
"""

import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_BOX_TONE,
    CMD_BOX_TONE_INFO,
    CMD_MBB_FEATURE,
    MBB_FEATURE_BOX_TONE,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiBoxToneHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

TONE_STATE_RQ = HuaweiSppPackage.read_rq(CMD_BOX_TONE, [2, 3]).to_bytes()
# 开关=1 支持=1
TONE_STATE_RESP = HuaweiSppPackage.change_rq(CMD_BOX_TONE, [(2, b"\x01"), (3, b"\x01")]).to_bytes()
TONE_STATE_RESP_OFF = HuaweiSppPackage.change_rq(CMD_BOX_TONE, [(2, b"\x00"), (3, b"\x01")]).to_bytes()

TONE_INFO_RQ = HuaweiSppPackage.read_rq(CMD_BOX_TONE_INFO, [1, 2, 3, 4]).to_bytes()
# 双耳在盒
TONE_INFO_RESP_IN_BOX = HuaweiSppPackage.change_rq(
    CMD_BOX_TONE_INFO, [(1, b"\x00"), (2, b"\x00"), (3, b"\x01"), (4, b"\x01")]
).to_bytes()
# 双耳佩戴（不在盒）
TONE_INFO_RESP_OUT = HuaweiSppPackage.change_rq(
    CMD_BOX_TONE_INFO, [(1, b"\x01"), (2, b"\x01"), (3, b"\x00"), (4, b"\x00")]
).to_bytes()

MBB_READ_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, b"")]
).to_bytes()
# 真机基线 payload：b0=01 b1=01 b2=07
F16_PAYLOAD = bytes.fromhex("010107020000000000006d01")
MBB_READ_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, F16_PAYLOAD)]
).to_bytes()
# payload 不足 12 字节 → 不支持开盖提示音
MBB_SHORT_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, b"\x01\x01")]
).to_bytes()

MASTER_OFF_RQ = HuaweiSppPackage.change_rq(CMD_BOX_TONE, [(1, 0)]).to_bytes()
# 整包写：b1=0（关开盖），b0 由当前总开关同步为 1
LID_OFF_PAYLOAD = bytes.fromhex("010007020000000000006d01")
LID_OFF_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, LID_OFF_PAYLOAD)]
).to_bytes()
LID_OFF_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, LID_OFF_PAYLOAD)]
).to_bytes()
# 整包写：b2=0x0a=10（音量，范围 0-15）
VOL_10_PAYLOAD = bytes.fromhex("01010a020000000000006d01")
VOL_10_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, VOL_10_PAYLOAD)]
).to_bytes()
VOL_10_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, VOL_10_PAYLOAD)]
).to_bytes()


def base_model():
    return {
        TONE_STATE_RQ: [TONE_STATE_RESP],
        TONE_INFO_RQ: [TONE_INFO_RESP_IN_BOX],
        MBB_READ_RQ: [MBB_READ_RESP],
    }


async def create_driver(model):
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiBoxToneHandler()],
        package_response_model=model,
    )
    await driver.start()
    return driver


@pytest.mark.asyncio
async def test_init_supported():
    driver = await create_driver(base_model())
    config = await driver.get_property("config", None)
    state = await driver.get_property("state", None)

    assert config["box_tone_supported"] == "true"
    assert config["box_tone_enabled"] == "true"
    assert config["box_tone_lid_supported"] == "true"
    assert config["box_tone_lid_enabled"] == "true"
    assert config["box_tone_lid_volume"] == "7"
    assert state["headset_in_box"] == "true"


@pytest.mark.asyncio
async def test_write_master_off():
    model = base_model()
    model[MASTER_OFF_RQ] = [TONE_STATE_RESP_OFF]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_enabled", "false")
    assert result is True
    assert await driver.get_property("config", "box_tone_enabled") == "false"


@pytest.mark.asyncio
async def test_write_lid_toggle_off():
    model = base_model()
    model[LID_OFF_RQ] = [LID_OFF_RESP]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_lid_enabled", "false")
    assert result is True
    assert await driver.get_property("config", "box_tone_lid_enabled") == "false"


@pytest.mark.asyncio
async def test_write_lid_volume():
    model = base_model()
    model[VOL_10_RQ] = [VOL_10_RESP]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_lid_volume", "10")
    assert result is True
    assert await driver.get_property("config", "box_tone_lid_volume") == "10"


@pytest.mark.asyncio
async def test_write_lid_volume_out_of_range():
    driver = await create_driver(base_model())

    assert await driver.set_property("config", "box_tone_lid_volume", "16") is False
    assert await driver.set_property("config", "box_tone_lid_volume", "50") is False
    assert await driver.get_property("config", "box_tone_lid_volume") == "7"


@pytest.mark.asyncio
async def test_write_requires_in_box():
    model = base_model()
    model[TONE_INFO_RQ] = [TONE_INFO_RESP_OUT]
    driver = await create_driver(model)
    assert await driver.get_property("state", "headset_in_box") == "false"

    assert await driver.set_property("config", "box_tone_enabled", "false") is False
    assert await driver.set_property("config", "box_tone_lid_enabled", "false") is False


@pytest.mark.asyncio
async def test_lid_unsupported_short_payload():
    model = base_model()
    model[MBB_READ_RQ] = [MBB_SHORT_RESP]
    driver = await create_driver(model)

    assert await driver.get_property("config", "box_tone_lid_supported") == "false"
    assert await driver.set_property("config", "box_tone_lid_enabled", "false") is False


# 写提示音 id：整包写 p2，b9..b10=大端 toneId，b11=select=1；
# devId 保留缓存 payload 中的设备上报值（真机为耳机自身 MAC），不随 toneId 重算。
# 内置音 id=18(0x12)，devId 沿用基线 020000000000
BUILTIN_ID_PAYLOAD = bytes.fromhex("010107020000000000001201")
BUILTIN_ID_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, BUILTIN_ID_PAYLOAD)]
).to_bytes()
BUILTIN_ID_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, BUILTIN_ID_PAYLOAD)]
).to_bytes()
# 自定义音 id=109(0x6d)，devId 同样沿用基线
CUSTOM_ID_PAYLOAD = bytes.fromhex("010107020000000000006d01")
CUSTOM_ID_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, CUSTOM_ID_PAYLOAD)]
).to_bytes()
CUSTOM_ID_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, CUSTOM_ID_PAYLOAD)]
).to_bytes()


@pytest.mark.asyncio
async def test_readback_tone_id():
    driver = await create_driver(base_model())

    assert await driver.get_property("config", "box_tone_id") == "109"
    assert await driver.get_property("config", "box_tone_device_id") == "020000000000"


@pytest.mark.asyncio
async def test_write_tone_id_builtin():
    model = base_model()
    model[BUILTIN_ID_RQ] = [BUILTIN_ID_RESP]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_id", "18")
    assert result is True
    assert await driver.get_property("config", "box_tone_id") == "18"
    assert await driver.get_property("config", "box_tone_device_id") == "020000000000"


@pytest.mark.asyncio
async def test_write_tone_id_custom():
    model = base_model()
    model[CUSTOM_ID_RQ] = [CUSTOM_ID_RESP]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_id", "109")
    assert result is True
    assert await driver.get_property("config", "box_tone_id") == "109"
    assert await driver.get_property("config", "box_tone_device_id") == "020000000000"


@pytest.mark.asyncio
async def test_write_tone_id_out_of_range():
    driver = await create_driver(base_model())

    assert await driver.set_property("config", "box_tone_id", "70000") is False
    assert await driver.set_property("config", "box_tone_id", "-1") is False
    assert await driver.set_property("config", "box_tone_id", "abc") is False
    assert await driver.get_property("config", "box_tone_id") == "109"


# select 位真机语义（2026-11-13 实测）：0=耳机内置固定音（仅 id 0「舒展」），1=耳机内已传音频
DEFAULT_TONE_PAYLOAD = bytes.fromhex("010107020000000000000000")
DEFAULT_TONE_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, DEFAULT_TONE_PAYLOAD)]
).to_bytes()
DEFAULT_TONE_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, DEFAULT_TONE_PAYLOAD)]
).to_bytes()


@pytest.mark.asyncio
async def test_write_tone_id_zero_selects_builtin():
    """选内置「舒展」(id 0) 必须写 select=0，否则设备继续播上一段已传音频。"""
    model = base_model()
    model[DEFAULT_TONE_RQ] = [DEFAULT_TONE_RESP]
    driver = await create_driver(model)

    assert await driver.set_property("config", "box_tone_id", "0") is True
    assert await driver.get_property("config", "box_tone_id") == "0"


@pytest.mark.asyncio
async def test_tone_id_switch_clears_status():
    """选 id 只是换槽位，不再提示「耳机里还没这段音频」；切回 id 0 也保持清空。"""
    id55_payload = bytes.fromhex("010107020000000000003701")
    id0_payload = bytes.fromhex("010107020000000000000000")
    model = base_model()
    model[DEFAULT_TONE_RQ] = [DEFAULT_TONE_RESP]
    model[HuaweiSppPackage.change_rq(
        CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, id55_payload)]).to_bytes()] = [
        HuaweiSppPackage.change_rq(
            CMD_MBB_FEATURE, [(1, b"\x10"), (2, id55_payload)]).to_bytes()]
    model[HuaweiSppPackage.change_rq(
        CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, id0_payload)]).to_bytes()] = [
        HuaweiSppPackage.change_rq(
            CMD_MBB_FEATURE, [(1, b"\x10"), (2, id0_payload)]).to_bytes()]
    driver = await create_driver(model)

    assert await driver.set_property("config", "box_tone_id", "55") is True
    assert (await driver.get_property("config", "box_tone_upload_status")) == ""

    assert await driver.set_property("config", "box_tone_id", "0") is True
    assert (await driver.get_property("config", "box_tone_upload_status")) == ""


@pytest.mark.asyncio
async def test_write_lid_volume_no_ack_keeps_local(monkeypatch):
    """0x2BB4 写不回 ACK 时不能把 TimeoutError 抛给界面（FreeClip 2 常见）。"""
    from openfreebuds.driver.huawei.handler import config_box_tone

    monkeypatch.setattr(config_box_tone, "_F16_WRITE_TIMEOUT", 0.2)
    monkeypatch.setattr(config_box_tone, "_MBB_READ_TIMEOUT", 0.2)

    model = base_model()  # 故意不给 VOL_10_RQ 任何响应
    driver = await create_driver(model)

    assert await driver.set_property("config", "box_tone_lid_volume", "10") is True
    # 写没回包，回读到的仍是设备上报的 7 → 界面以设备为准
    assert await driver.get_property("config", "box_tone_lid_volume") == "7"


@pytest.mark.asyncio
async def test_write_lid_volume_no_ack_and_no_reread(monkeypatch):
    """写和回读都不回包：不抛异常，保留本地值。"""
    from openfreebuds.driver.huawei.handler import config_box_tone

    monkeypatch.setattr(config_box_tone, "_F16_WRITE_TIMEOUT", 0.2)
    monkeypatch.setattr(config_box_tone, "_MBB_READ_TIMEOUT", 0.2)

    model = base_model()
    driver = await create_driver(model)
    # 初始化之后把回读也堵住，模拟充电盒休眠、整个链路都不应答
    model[MBB_READ_RQ] = []

    assert await driver.set_property("config", "box_tone_lid_volume", "10") is True
    assert await driver.get_property("config", "box_tone_lid_volume") == "7"


@pytest.mark.asyncio
async def test_write_lid_volume_same_value_skipped():
    """拖到原值不该再打扰耳机。"""
    model = base_model()
    driver = await create_driver(model)
    before = len(driver.package_log)

    assert await driver.set_property("config", "box_tone_lid_volume", "7") is True
    assert len(driver.package_log) == before
