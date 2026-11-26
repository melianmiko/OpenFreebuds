"""Smart-charge handler tests (0x2BB4 MBB featureId 4).

Protocol derived from FeatureMbbState$g0: query 01 01 04, write
01 01 04 02 01 <0/1>. The response's parameter 2 carries the switch state.
"""

import pytest

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_SMART_CHARGE
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiSmartChargeHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

READ_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_SMART_CHARGE)]
).to_bytes()
READ_RESP_ON = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x04"), (2, b"\x01")]
).to_bytes()
READ_RESP_OFF = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x04"), (2, b"\x00")]
).to_bytes()
READ_RESP_NO_STATE = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x04")]
).to_bytes()
WRITE_OFF_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_SMART_CHARGE), (2, 0)]
).to_bytes()
WRITE_ON_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_SMART_CHARGE), (2, 1)]
).to_bytes()


async def create_driver(model):
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiSmartChargeHandler()],
        package_response_model=model,
    )
    await driver.start()
    return driver


@pytest.mark.asyncio
async def test_read_supported_on():
    driver = await create_driver({READ_RQ: [READ_RESP_ON]})
    props = await driver.get_property("config", None)

    assert props["smart_charge_supported"] == "true"
    assert props["smart_charge"] == "true"


@pytest.mark.asyncio
async def test_write_off_and_on():
    driver = await create_driver({
        READ_RQ: [READ_RESP_ON],
        WRITE_OFF_RQ: [READ_RESP_OFF],
        WRITE_ON_RQ: [READ_RESP_ON],
    })

    assert await driver.set_property("config", "smart_charge", "false") is True
    assert await driver.get_property("config", "smart_charge") == "false"
    assert await driver.set_property("config", "smart_charge", "true") is True
    assert await driver.get_property("config", "smart_charge") == "true"


@pytest.mark.asyncio
async def test_read_without_state_is_unsupported():
    driver = await create_driver({READ_RQ: [READ_RESP_NO_STATE]})
    assert await driver.get_property("config", "smart_charge_supported") == "false"


@pytest.mark.asyncio
async def test_write_unsupported_is_rejected():
    driver = await create_driver({READ_RQ: [READ_RESP_NO_STATE]})
    assert await driver.set_property("config", "smart_charge", "true") is False
