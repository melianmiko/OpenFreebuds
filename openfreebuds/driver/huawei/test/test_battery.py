import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.constants import CMD_BATTERY_NOTIFY
from openfreebuds.driver.huawei.handler import OfbHuaweiBatteryHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

GET_BATTERY_RQ = bytes.fromhex("5a0009000108010002000300fbb9")
GET_BATTERY_RESP_BASE = bytes.fromhex("5a0014000108010140020310203003030001000402140a1461")
GET_BATTERY_RESP_LEGACY = bytes.fromhex("5a0009000108010140030100ed2e")
GET_BATTERY_RESP_PRO5 = HuaweiSppPackage(b"\x01\x08", [
    (1, b"\x58"),
    (2, b"\x58\x5d\x3a"),
    (3, b"\x00\x01\x00"),
    (4, b"\x0a\x14"),
    (5, b"\x00\x01"),
    (6, b"\x0a"),
]).to_bytes()


async def create_driver(resp):
    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiBatteryHandler()
        ],
        package_response_model={
            GET_BATTERY_RQ: [resp]
        }
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
async def test_battery_pro5_response():
    driver = await create_driver(GET_BATTERY_RESP_PRO5)
    props = await driver.get_property("battery", None)

    assert props["left"] == 88
    assert props["right"] == 93
    assert props["case"] == 58
    assert props["global"] == 88
    assert props["is_charging"] == "true"


@pytest.mark.asyncio
async def test_battery_partial_notification_keeps_tws_levels():
    driver = await create_driver(GET_BATTERY_RESP_BASE)

    await driver._handle_raw_pkg(HuaweiSppPackage(CMD_BATTERY_NOTIFY, [
        (1, b"\x41"),
        (3, b"\x00"),
    ]).to_bytes())
    props = await driver.get_property("battery", None)

    assert props["left"] == 0x10
    assert props["right"] == 0x20
    assert props["case"] == 0x30
    assert props["global"] == 0x41
    assert props["is_charging"] == "false"
