import asyncio

import pytest

from openfreebuds.driver.huawei.driver.debug import OfbDriverHuaweiGenericLoggable
from openfreebuds.driver.huawei.package import HuaweiSppPackage


@pytest.mark.asyncio
async def test_recv_loop_reads_full_frames_without_desync():
    first_pkg = HuaweiSppPackage(b"\x2b\xac", [(1, 0), (127, b"\x00\x00\xba")]).to_bytes()
    second_pkg = HuaweiSppPackage(b"\x2b\xb4", [(1, 4), (2, 1)]).to_bytes()

    reader = asyncio.StreamReader()
    reader.feed_data(first_pkg + second_pkg)
    reader.feed_eof()

    driver = OfbDriverHuaweiGenericLoggable("")
    await driver._loop_recv(reader)

    assert driver.package_log == [
        ("recv", first_pkg),
        ("recv", second_pkg),
    ]