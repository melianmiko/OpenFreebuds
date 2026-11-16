import pytest

from openfreebuds.driver.huawei.constants import CMD_BOX_TONE_INFO
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiBatteryHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

GET_BATTERY_RQ = bytes.fromhex("5a0009000108010002000300fbb9")
GET_BATTERY_RESP_BASE = bytes.fromhex("5a0014000108010140020310203003030001000402140a1461")
GET_BATTERY_RESP_LEGACY = bytes.fromhex("5a0009000108010140030100ed2e")

GET_IN_BOX_RQ = HuaweiSppPackage.read_rq(CMD_BOX_TONE_INFO, [1, 2, 3, 4]).to_bytes()
GET_IN_BOX_RESP = HuaweiSppPackage.change_rq(
    CMD_BOX_TONE_INFO,
    [(1, b"\x00"), (2, b"\x01"), (3, b"\x01"), (4, b"\x01")],
).to_bytes()


async def create_driver(resp, in_box_resp=None):
    response_model = {
        GET_BATTERY_RQ: [resp],
    }
    if in_box_resp is not None:
        response_model[GET_IN_BOX_RQ] = [in_box_resp]

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiBatteryHandler()
        ],
        package_response_model=response_model
    )

    await driver.start()
    await driver.send_package(HuaweiSppPackage.from_bytes(GET_BATTERY_RQ))

    assert driver.package_log[0] == ("send", GET_BATTERY_RQ)
    assert driver.package_log[1] == ("recv", resp)

    return driver


@pytest.mark.asyncio
async def test_battery_base():
    driver = await create_driver(GET_BATTERY_RESP_BASE)
    props = await driver.get_property("battery", None)

    assert props["left"] == 0x10
    assert props["right"] == 0x20
    assert props["case"] == 0x30
    assert props["global"] == 0x40
    assert props["is_charging"] == "true"


@pytest.mark.asyncio
async def test_battery_legacy():
    driver = await create_driver(GET_BATTERY_RESP_LEGACY)
    props = await driver.get_property("battery", None)

    assert "left" not in props
    assert props["global"] == 0x40
    assert props["is_charging"] == "false"


@pytest.mark.asyncio
async def test_battery_in_box():
    driver = await create_driver(GET_BATTERY_RESP_BASE, in_box_resp=GET_IN_BOX_RESP)
    props = await driver.get_property("battery", None)
    state = await driver.get_property("state", None)

    assert props["in_box"] == "true"
    assert props["left_in_box"] == "true"
    assert props["right_in_box"] == "true"
    assert props["left_in_ear"] == "false"
    assert props["right_in_ear"] == "true"
    assert state["headset_in_box"] == "true"
    assert state["left_in_ear"] == "false"
    assert state["right_in_ear"] == "true"
    assert state["in_ear"] == "true"
