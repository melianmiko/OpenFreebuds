import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiConfigAutoPauseHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


@pytest.mark.asyncio
async def test_auto_pause():
    get_auto_pause_rq = bytes.fromhex("5a0005002b110100772a")
    get_auto_pause_resp = bytes.fromhex("5a0006002b11010100cfc3")
    set_auto_pause_on_req = bytes.fromhex("5a0006002b10010101a956")
    set_auto_pause_on_resp = bytes.fromhex("5a0009002b107f04000186a0729d")

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiConfigAutoPauseHandler()
        ],
        package_response_model={
            get_auto_pause_rq: [get_auto_pause_resp],
            set_auto_pause_on_req: [set_auto_pause_on_resp],
        }
    )

    await driver.start()

    # Read
    await driver.send_package(HuaweiSppPackage.from_bytes(get_auto_pause_rq))
    assert await driver.get_property("config", "auto_pause") == "false"

    # Write
    await driver.set_property("config", "auto_pause", "true")
    assert await driver.get_property("config", "auto_pause") == "true"
