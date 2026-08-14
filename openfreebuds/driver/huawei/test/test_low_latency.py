import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiLowLatencyPreferenceHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


@pytest.mark.asyncio
async def test_low_latency():
    read_rq = bytes.fromhex("5a0005002b6c0200b820")
    read_resp = bytes.fromhex("5a0006002b6c020100ed60")
    read_resp_after_write = bytes.fromhex("5a0006002b6c020101fd")
    write_rq = bytes.fromhex("5a0006002b6c010101a411")
    write_resp = bytes.fromhex("5a0009002b6c7f04000186a0a497")

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiLowLatencyPreferenceHandler()
        ],
        package_response_model={
            read_rq: [read_resp],
            write_rq: [write_resp],
        }
    )

    await driver.start()

    # Read
    # await driver.send_package(HuaweiSppPackage.from_bytes(read_rq))
    assert await driver.get_property("config", "low_latency") == "false"

    # Write
    driver.package_response_model[read_rq] = [read_resp_after_write]
    await driver.set_property("config", "low_latency", "true")
    assert await driver.get_property("config", "low_latency") == "true"


@pytest.mark.asyncio
async def test_low_latency_writes_param_1_and_reads_state_back():
    """
    Devices report the toggle on parameter 2 but only accept writes on parameter 1.
    A write to parameter 2 is answered with a success code and then ignored, so the
    handler must send parameter 1 and trust the follow-up read over the request.
    """
    read_rq = bytes.fromhex("5a0005002b6c0200b820")
    read_resp = bytes.fromhex("5a0006002b6c020100ed60")
    write_rq = bytes.fromhex("5a0006002b6c010101a411")
    write_resp = bytes.fromhex("5a0009002b6c7f04000186a0a497")

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiLowLatencyPreferenceHandler()
        ],
        package_response_model={
            read_rq: [read_resp],
            write_rq: [write_resp],
        }
    )

    await driver.start()
    await driver.set_property("config", "low_latency", "true")

    assert HuaweiSppPackage.change_rq(b"\x2b\x6c", [(1, b"\x01")]).to_bytes() == write_rq
    assert ("send", write_rq) in driver.package_log

    # Device kept reporting "off", so the property must not follow the request.
    assert await driver.get_property("config", "low_latency") == "false"
