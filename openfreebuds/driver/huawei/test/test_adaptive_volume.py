"""自适应音量 handler 测试（0x2BB4 MBB featureId 2）

协议依据 2026-11-13 FreeClip 2 真机标定：
  读：01 01 02 02 00 03 00 → p2=开关 p3=灵敏度
  写开关：01 01 02 02 01 <0/1>
  写灵敏度：01 01 02 03 01 <0/1/2>
"""

import pytest

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_ADAPTIVE_VOLUME
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiAdaptiveVolumeHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

READ_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_ADAPTIVE_VOLUME), (2, b""), (3, b"")]
).to_bytes()
# feature=2, 开关=1, 灵敏度=1(default)
READ_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x02"), (2, b"\x01"), (3, b"\x01")]
).to_bytes()
# 开关=0
READ_RESP_OFF = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x02"), (2, b"\x00"), (3, b"\x01")]
).to_bytes()
# 仅回显 feature，无开关字段 → 视为不支持
READ_RESP_NO_STATE = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x02")]
).to_bytes()

WRITE_OFF_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_ADAPTIVE_VOLUME), (2, 0)]
).to_bytes()
WRITE_LEVEL_HIGH_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_ADAPTIVE_VOLUME), (3, 2)]
).to_bytes()
RESP_LEVEL_HIGH = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x02"), (2, b"\x01"), (3, b"\x02")]
).to_bytes()


async def create_driver(model):
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiAdaptiveVolumeHandler()],
        package_response_model=model,
    )
    await driver.start()
    return driver


@pytest.mark.asyncio
async def test_read_supported():
    driver = await create_driver({READ_RQ: [READ_RESP]})
    props = await driver.get_property("sound", None)

    assert props["adaptive_volume_supported"] == "true"
    assert props["adaptive_volume"] == "true"
    assert props["adaptive_volume_level"] == "default"
    assert props["adaptive_volume_level_options"] == "low,default,high"


@pytest.mark.asyncio
async def test_write_toggle_off():
    driver = await create_driver({READ_RQ: [READ_RESP], WRITE_OFF_RQ: [READ_RESP_OFF]})
    result = await driver.set_property("sound", "adaptive_volume", "false")

    assert result is True
    assert await driver.get_property("sound", "adaptive_volume") == "false"


@pytest.mark.asyncio
async def test_write_level_high():
    driver = await create_driver({READ_RQ: [READ_RESP], WRITE_LEVEL_HIGH_RQ: [RESP_LEVEL_HIGH]})
    result = await driver.set_property("sound", "adaptive_volume_level", "high")

    assert result is True
    assert await driver.get_property("sound", "adaptive_volume_level") == "high"


@pytest.mark.asyncio
async def test_write_level_requires_enabled():
    driver = await create_driver({READ_RQ: [READ_RESP_OFF]})
    assert await driver.get_property("sound", "adaptive_volume") == "false"

    result = await driver.set_property("sound", "adaptive_volume_level", "high")
    assert result is False


@pytest.mark.asyncio
async def test_write_unsupported():
    driver = await create_driver({READ_RQ: [READ_RESP_NO_STATE]})
    result = await driver.set_property("sound", "adaptive_volume", "true")
    assert result is False