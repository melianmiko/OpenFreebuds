"""Noisy-environment media volume boost tests (official big_volume_new).

Protocol from the official BigVolumeRepository:
  new support query  2b 88 02 00 -> 2b 88 02 01 <0/1>
  new state query    2b 88 01 00 -> 2b 88 01 01 <0/1>
  new state write    2b 87 01 01 <0/1>
  legacy state query 2b 80 01 00 -> 2b 80 01 01 <0/1>
  legacy state write 2b 7f 01 01 <0/1>
"""

import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_BIG_VOLUME_LEGACY_QUERY,
    CMD_BIG_VOLUME_LEGACY_WRITE,
    CMD_BIG_VOLUME_QUERY,
    CMD_BIG_VOLUME_WRITE,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiBigVolumeHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

NEW_SUPPORT_RQ = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_QUERY, [(2, b"")]).to_bytes()
STATE_RQ = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_QUERY, [(1, b"")]).to_bytes()
LEGACY_RQ = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_LEGACY_QUERY, [(1, b"")]).to_bytes()

NEW_SUPPORTED = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_QUERY, [(2, b"\x01")]).to_bytes()
NEW_UNSUPPORTED = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_QUERY, [(2, b"\x00")]).to_bytes()
STATE_ON = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_QUERY, [(1, b"\x01")]).to_bytes()
STATE_OFF = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_QUERY, [(1, b"\x00")]).to_bytes()
LEGACY_ON = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_LEGACY_QUERY, [(1, b"\x01")]).to_bytes()
LEGACY_OFF = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_LEGACY_QUERY, [(1, b"\x00")]).to_bytes()
LEGACY_NO_STATE = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_LEGACY_QUERY, [(1, b"")]).to_bytes()

SET_NEW_OFF_RQ = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_WRITE, [(1, 0)]).to_bytes()
SET_LEGACY_ON_RQ = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_LEGACY_WRITE, [(1, 1)]).to_bytes()
ACK_NEW = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_WRITE, [(1, b"")]).to_bytes()
ACK_LEGACY = HuaweiSppPackage.change_rq(
    CMD_BIG_VOLUME_LEGACY_WRITE, [(1, b"")]).to_bytes()


class SequencingFixture(FbDriverHuaweiGenericFixture):
    """Fake driver that consumes one response list per identical request."""

    def __init__(self, handlers, response_sequences):
        super().__init__(handlers=handlers, package_response_model={})
        self.response_sequences = response_sequences

    async def _send_nowait(self, pkg: HuaweiSppPackage):
        rx = pkg.to_bytes()
        self.package_log.append(("send", rx))
        queue = self.response_sequences.get(rx)
        if queue:
            for tx in queue.pop(0):
                await self._handle_raw_pkg(tx)


async def create_driver(response_sequences):
    driver = SequencingFixture(
        handlers=[OfbHuaweiBigVolumeHandler()],
        response_sequences=response_sequences,
    )
    await driver.start()
    return driver


@pytest.mark.asyncio
async def test_read_new_protocol_on():
    driver = await create_driver({
        NEW_SUPPORT_RQ: [[NEW_SUPPORTED]],
        STATE_RQ: [[STATE_ON]],
    })
    props = await driver.get_property("sound", None)

    assert props["big_volume_supported"] == "true"
    assert props["big_volume"] == "true"


@pytest.mark.asyncio
async def test_write_new_protocol_off():
    driver = await create_driver({
        NEW_SUPPORT_RQ: [[NEW_SUPPORTED]],
        STATE_RQ: [[STATE_ON], [STATE_OFF]],
        SET_NEW_OFF_RQ: [[ACK_NEW]],
    })

    assert await driver.get_property("sound", "big_volume") == "true"
    assert await driver.set_property("sound", "big_volume", "false") is True
    assert await driver.get_property("sound", "big_volume") == "false"


@pytest.mark.asyncio
async def test_read_legacy_protocol_off():
    driver = await create_driver({
        NEW_SUPPORT_RQ: [[NEW_UNSUPPORTED]],
        LEGACY_RQ: [[LEGACY_OFF]],
    })
    props = await driver.get_property("sound", None)

    assert props["big_volume_supported"] == "true"
    assert props["big_volume"] == "false"


@pytest.mark.asyncio
async def test_write_legacy_protocol_on():
    driver = await create_driver({
        NEW_SUPPORT_RQ: [[NEW_UNSUPPORTED]],
        LEGACY_RQ: [[LEGACY_OFF], [LEGACY_ON]],
        SET_LEGACY_ON_RQ: [[ACK_LEGACY]],
    })

    assert await driver.set_property("sound", "big_volume", "true") is True
    assert await driver.get_property("sound", "big_volume") == "true"


@pytest.mark.asyncio
async def test_unsupported_when_no_state_field():
    driver = await create_driver({
        NEW_SUPPORT_RQ: [[NEW_UNSUPPORTED]],
        LEGACY_RQ: [[LEGACY_NO_STATE]],
    })

    assert await driver.get_property("sound", "big_volume_supported") == "false"
    assert await driver.set_property("sound", "big_volume", "true") is False
