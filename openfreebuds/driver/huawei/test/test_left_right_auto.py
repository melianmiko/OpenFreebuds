"""Left/right auto-switch handler tests (read 0x2B9A, write 0x2B99).

Protocol derived from the official LeftRightEarRecognitionCard:
read 2b 9a 01 00, write 2b 99 01 01 <0/1>. Parameter 1 carries the switch state.
"""

import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_LEFT_RIGHT_AUTO,
    CMD_LEFT_RIGHT_AUTO_WRITE,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.driver.per_model.free_clip import OfbDriverHuaweiFreeClip
from openfreebuds.driver.huawei.driver.per_model.free_clip_2 import OfbDriverHuaweiFreeClip2
from openfreebuds.driver.huawei.driver.per_model.free_clip_2_s import OfbDriverHuaweiFreeClip2S
from openfreebuds.driver.huawei.driver.per_model.w_buds import OfbDriverHuaweiWBuds
from openfreebuds.driver.huawei.handler import OfbHuaweiLeftRightAutoHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

READ_RQ = HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_AUTO, [(1, b"")]).to_bytes()
READ_RESP_ON = HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_AUTO, [(1, b"\x01")]).to_bytes()
READ_RESP_OFF = HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_AUTO, [(1, b"\x00")]).to_bytes()
READ_RESP_EMPTY = HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_AUTO, [(1, b"")]).to_bytes()
WRITE_ACK = HuaweiSppPackage.change_rq(
    CMD_LEFT_RIGHT_AUTO_WRITE,
    [(127, b"\x00\x01\x86\xa0")],
).to_bytes()
WRITE_OFF_RQ = HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_AUTO_WRITE, [(1, 0)]).to_bytes()
WRITE_ON_RQ = HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_AUTO_WRITE, [(1, 1)]).to_bytes()


async def create_driver(model):
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiLeftRightAutoHandler()],
        package_response_model=model,
    )
    await driver.start()
    return driver


@pytest.mark.asyncio
async def test_read_supported_on():
    driver = await create_driver({READ_RQ: [READ_RESP_ON]})
    props = await driver.get_property("config", None)

    assert props["left_right_auto_supported"] == "true"
    assert props["left_right_auto"] == "true"


@pytest.mark.asyncio
async def test_read_supported_off():
    driver = await create_driver({READ_RQ: [READ_RESP_OFF]})
    assert await driver.get_property("config", "left_right_auto_supported") == "true"
    assert await driver.get_property("config", "left_right_auto") == "false"


@pytest.mark.asyncio
async def test_write_off_and_on():
    driver = await create_driver({
        READ_RQ: [READ_RESP_ON],
        WRITE_OFF_RQ: [WRITE_ACK],
        WRITE_ON_RQ: [WRITE_ACK],
    })

    assert await driver.set_property("config", "left_right_auto", "false") is True
    assert await driver.get_property("config", "left_right_auto") == "false"
    assert await driver.set_property("config", "left_right_auto", "true") is True
    assert await driver.get_property("config", "left_right_auto") == "true"


@pytest.mark.asyncio
async def test_write_uses_0x2b99_command():
    driver = await create_driver({
        READ_RQ: [READ_RESP_ON],
        WRITE_OFF_RQ: [WRITE_ACK],
    })

    assert await driver.set_property("config", "left_right_auto", "false") is True
    assert ("send", WRITE_OFF_RQ) in driver.package_log


@pytest.mark.asyncio
async def test_read_without_state_is_unsupported():
    driver = await create_driver({READ_RQ: [READ_RESP_EMPTY]})
    assert await driver.get_property("config", "left_right_auto_supported") == "false"


@pytest.mark.asyncio
async def test_write_unsupported_is_rejected():
    driver = await create_driver({READ_RQ: [READ_RESP_EMPTY]})
    assert await driver.set_property("config", "left_right_auto", "true") is False


@pytest.mark.parametrize("driver_cls", [
    OfbDriverHuaweiFreeClip,
    OfbDriverHuaweiFreeClip2,
    OfbDriverHuaweiFreeClip2S,
    OfbDriverHuaweiWBuds,
])
def test_left_right_handler_is_mounted(driver_cls):
    driver = driver_cls("00:11:22:33:44:55")
    assert any(isinstance(handler, OfbHuaweiLeftRightAutoHandler) for handler in driver.handlers)
