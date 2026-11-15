"""「查找耳机」handler 测试（0x2B5D 设置 / 0x2B5E 查询）

协议依据 2026-11-14 FreeClip 2 真机标定：
  发 2b 5d 01 02 <side> <state>   side 0=左 1=右 2=双，state 0=响 1=停
  查 2b 5e 01 01 <side>           回 2b 5e 02 02 <side> <state>（1=空闲，0=响铃中）
"""

import asyncio

import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_FIND_EARBUD_SET,
    CMD_FIND_EARBUD_STATE,
    FIND_EARBUD_SIDE_BOTH,
    FIND_EARBUD_SIDE_LEFT,
    FIND_EARBUD_SIDE_RIGHT,
    FIND_EARBUD_STATE_RING,
    FIND_EARBUD_STATE_STOP,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiFindEarbudHandler
from openfreebuds.driver.huawei.handler.find_earbud import (
    build_find_rq,
    build_find_state_rq,
    parse_find_state,
)
from openfreebuds.driver.huawei.package import HuaweiSppPackage


def state_rq(side: int) -> bytes:
    return build_find_state_rq(side).to_bytes()


def state_resp(side: int, state: int) -> bytes:
    return HuaweiSppPackage.change_rq(CMD_FIND_EARBUD_STATE, [
        (2, bytes([side, state])),
    ]).to_bytes()


def find_rq(side: int, state: int) -> bytes:
    return build_find_rq(side, state).to_bytes()


def find_resp(side: int) -> bytes:
    return HuaweiSppPackage.change_rq(CMD_FIND_EARBUD_SET, [
        (2, bytes([side, 0])),
    ]).to_bytes()


def base_model():
    return {
        state_rq(FIND_EARBUD_SIDE_LEFT): [state_resp(FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_STATE_STOP)],
        state_rq(FIND_EARBUD_SIDE_RIGHT): [state_resp(FIND_EARBUD_SIDE_RIGHT, FIND_EARBUD_STATE_STOP)],
    }


async def create_driver(model):
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiFindEarbudHandler()],
        package_response_model=model,
    )
    await driver.start()
    return driver


def test_build_find_rq_matches_verified_frame():
    # 真机帧：2b 5d 01 02 00 00（左耳开响）
    body = build_find_rq(FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_STATE_RING).to_bytes()
    assert body[4:-2] == bytes.fromhex("2b5d01020000")


def test_build_stop_and_both_frames():
    assert build_find_rq(FIND_EARBUD_SIDE_BOTH, FIND_EARBUD_STATE_STOP).to_bytes()[4:-2] == \
           bytes.fromhex("2b5d01020201")
    assert build_find_state_rq(FIND_EARBUD_SIDE_RIGHT).to_bytes()[4:-2] == bytes.fromhex("2b5e010101")


def test_parse_find_state():
    pkg = HuaweiSppPackage.from_bytes(state_resp(FIND_EARBUD_SIDE_BOTH, FIND_EARBUD_STATE_RING))
    assert parse_find_state(pkg) == (FIND_EARBUD_SIDE_BOTH, FIND_EARBUD_STATE_RING)

    pkg = HuaweiSppPackage.from_bytes(
        HuaweiSppPackage.change_rq(CMD_FIND_EARBUD_STATE, [(2, b"\x01")]).to_bytes())
    assert parse_find_state(pkg) is None


@pytest.mark.asyncio
async def test_init_reports_supported_idle():
    driver = await create_driver(base_model())
    config = await driver.get_property("config", None)
    state = await driver.get_property("state", None)

    assert config["find_earbud_supported"] == "true"
    assert state["find_earbud_ringing"] == ""


@pytest.mark.asyncio
async def test_ring_both_sends_side_2():
    model = base_model()
    model[find_rq(FIND_EARBUD_SIDE_BOTH, FIND_EARBUD_STATE_RING)] = [find_resp(FIND_EARBUD_SIDE_BOTH)]
    driver = await create_driver(model)

    assert await driver.set_property("config", "find_earbud", "ring") is True
    assert await driver.get_property("state", "find_earbud_ringing") == "left,right"


def test_parse_rejects_set_ack():
    """0x5D 的 ACK（2b 5d 02 02 <side> 00）末位是 result，不能被当成状态帧。"""
    ack = HuaweiSppPackage.from_bytes(find_resp(FIND_EARBUD_SIDE_LEFT))
    assert parse_find_state(ack) is None

    ack = HuaweiSppPackage.from_bytes(
        HuaweiSppPackage.change_rq(CMD_FIND_EARBUD_SET, [(2, b"\x02\x00")]).to_bytes())
    assert parse_find_state(ack) is None


@pytest.mark.asyncio
async def test_set_ack_does_not_clear_ringing_state():
    """按停止后设备先回 0x5D ACK（末位 00），界面不能被它翻成"响铃中"。"""
    model = base_model()
    model[find_rq(FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_STATE_STOP)] = [find_resp(FIND_EARBUD_SIDE_LEFT)]
    model[find_rq(FIND_EARBUD_SIDE_RIGHT, FIND_EARBUD_STATE_STOP)] = [find_resp(FIND_EARBUD_SIDE_RIGHT)]
    driver = await create_driver(model)

    handler = driver.handlers[0]
    handler._ringing[FIND_EARBUD_SIDE_LEFT] = True
    handler._ringing[FIND_EARBUD_SIDE_RIGHT] = True
    await handler._publish_ringing()

    assert await driver.set_property("config", "find_earbud", "stop") is True
    assert await driver.get_property("state", "find_earbud_ringing") == ""


@pytest.mark.asyncio
async def test_stop_left_only_sends_one_side():
    model = base_model()
    model[find_rq(FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_STATE_STOP)] = [find_resp(FIND_EARBUD_SIDE_LEFT)]
    driver = await create_driver(model)

    handler = driver.handlers[0]
    handler._ringing[FIND_EARBUD_SIDE_LEFT] = True
    handler._ringing[FIND_EARBUD_SIDE_RIGHT] = True
    await handler._publish_ringing()

    assert await driver.set_property("config", "find_earbud", "stop:left") is True
    # 只停左耳，右耳仍在响
    assert await driver.get_property("state", "find_earbud_ringing") == "right"


@pytest.mark.asyncio
async def test_ring_does_not_wait_for_ack():
    """设备不回 SET 的 ACK 时也不能抛超时（真机上这条超时会把 Qt 端带崩）。"""
    model = base_model()
    driver = await create_driver(model)

    result = await asyncio.wait_for(
        driver.set_property("config", "find_earbud", "ring:left"), timeout=1.0)
    assert result is True
    assert await driver.get_property("state", "find_earbud_ringing") == "left"


@pytest.mark.asyncio
async def test_stop_sends_both_sides():
    model = base_model()
    model[find_rq(FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_STATE_STOP)] = [find_resp(FIND_EARBUD_SIDE_LEFT)]
    model[find_rq(FIND_EARBUD_SIDE_RIGHT, FIND_EARBUD_STATE_STOP)] = [find_resp(FIND_EARBUD_SIDE_RIGHT)]
    driver = await create_driver(model)

    assert await driver.set_property("config", "find_earbud", "stop") is True
    assert await driver.get_property("state", "find_earbud_ringing") == ""
