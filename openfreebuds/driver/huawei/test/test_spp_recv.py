import asyncio

import pytest

from openfreebuds.driver.huawei.driver.debug import OfbDriverHuaweiGenericLoggable
from openfreebuds.driver.huawei.package import HuaweiSppPackage


async def _receive(data: bytes):
    driver = OfbDriverHuaweiGenericLoggable("")
    reader = asyncio.StreamReader()
    reader.feed_data(data)
    reader.feed_eof()
    await asyncio.wait_for(driver._loop_recv(reader), 2)
    return [pkg for kind, pkg in driver.package_log if kind == "recv"]


@pytest.mark.asyncio
async def test_back_to_back_frames():
    # Real FreeBuds 7i burst after selecting dynamic ANC: ack, 2b2c event, new ANC state
    frames = [
        bytes.fromhex("5a0006002b040201003171"),
        HuaweiSppPackage(b"\x2b\x2c", [(1, b"\x00")]).to_bytes(),
        bytes.fromhex("5a0007002b2a010203015043"),
    ]
    assert await _receive(b"".join(frames)) == frames


@pytest.mark.asyncio
async def test_garbage_before_frame():
    frame = bytes.fromhex("5a0007002b2a010203015043")
    assert await _receive(b"\x00\x13" + frame) == [frame]
