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
async def test_low_latency_can_write_state_param_2():
    read_rq = bytes.fromhex("5a0005002b6c0200b820")
    read_resp = bytes.fromhex("5a0006002b6c020100ed60")
    write_rq = HuaweiSppPackage.change_rq(b"\x2b\x6c", [(2, 1)]).to_bytes()
    write_resp = HuaweiSppPackage(b"\x2b\x6c", [(2, 1)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiLowLatencyPreferenceHandler(write_param=2)
        ],
        package_response_model={
            read_rq: [read_resp],
            write_rq: [write_resp],
        }
    )

    await driver.start()

    driver.package_response_model[read_rq] = [write_resp]
    await driver.set_property("config", "low_latency", "true")

    assert await driver.get_property("config", "low_latency") == "true"
    assert driver.package_log[0] == ("send", write_rq)
