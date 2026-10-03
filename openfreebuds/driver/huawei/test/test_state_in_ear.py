import pytest

from openfreebuds.driver.huawei.constants import CMD_WEARING_STATUS
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler.state_in_ear import OfbHuaweiStateInEarHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


def wearing_status_read_model(left: int = 0, right: int = 0, left_box: int = 0, right_box: int = 0):
    read_rq = HuaweiSppPackage.read_rq(CMD_WEARING_STATUS, [1, 2, 3, 4]).to_bytes()
    read_resp = HuaweiSppPackage(CMD_WEARING_STATUS, [
        (1, left),
        (2, right),
        (3, left_box),
        (4, right_box),
    ]).to_bytes()
    return {read_rq: [read_resp]}


@pytest.mark.asyncio
async def test_wearing_status_is_read_on_init():
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiStateInEarHandler()],
        package_response_model=wearing_status_read_model(left=1, right=1),
    )
    await driver.start()

    assert await driver.get_property("state", "in_ear") == "true"
    assert await driver.get_property("state", "in_ear_left") == "true"
    assert await driver.get_property("state", "in_ear_right") == "true"


@pytest.mark.asyncio
async def test_wearing_status_notification_updates_pro_5_in_ear_state():
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiStateInEarHandler()],
        package_response_model=wearing_status_read_model(),
    )
    await driver.start()

    await driver._handle_raw_pkg(HuaweiSppPackage(CMD_WEARING_STATUS, [
        (1, 1),
        (2, 0),
        (3, 0),
        (4, 1),
    ]).to_bytes())

    assert await driver.get_property("state", "in_ear") == "true"
    assert await driver.get_property("state", "in_ear_left") == "true"
    assert await driver.get_property("state", "in_ear_right") == "false"
    assert await driver.get_property("state", "in_box_left") == "false"
    assert await driver.get_property("state", "in_box_right") == "true"


@pytest.mark.asyncio
async def test_legacy_in_ear_notification_still_updates_state():
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiStateInEarHandler()],
        package_response_model=wearing_status_read_model(),
    )
    await driver.start()

    await driver._handle_raw_pkg(HuaweiSppPackage(b"+\x03", [(8, 1)]).to_bytes())

    assert await driver.get_property("state", "in_ear") == "true"