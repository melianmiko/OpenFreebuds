import pytest

from openfreebuds.driver.huawei.constants import CMD_SMART_CALL_VOLUME_READ, CMD_SMART_CALL_VOLUME_WRITE
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiSmartCallVolumeHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


HUAWEI_UNSUPPORTED_ERROR = b"\x00\x01\x86\xa3"


@pytest.mark.asyncio
async def test_smart_call_volume_query_and_set():
    get_rq = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_READ, [(1, b"")], resp=CMD_SMART_CALL_VOLUME_READ).to_bytes()
    get_resp = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_READ, [(1, 0)]).to_bytes()
    set_on_rq = HuaweiSppPackage.change_rq(CMD_SMART_CALL_VOLUME_WRITE, [(1, 1)]).to_bytes()
    set_on_resp = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_WRITE, [(1, 1)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiSmartCallVolumeHandler()],
        package_response_model={
            get_rq: [get_resp],
            set_on_rq: [set_on_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("sound", "smart_call_volume") == "false"

    await driver.set_property("sound", "smart_call_volume", "true")

    assert await driver.get_property("sound", "smart_call_volume") == "true"
    assert driver.package_log[0] == ("send", set_on_rq)


@pytest.mark.asyncio
async def test_smart_call_volume_hides_when_unsupported():
    get_rq = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_READ, [(1, b"")], resp=CMD_SMART_CALL_VOLUME_READ).to_bytes()
    get_resp = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_READ, [(1, 2)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiSmartCallVolumeHandler()],
        package_response_model={get_rq: [get_resp]},
    )

    await driver.start()

    assert await driver.get_property("sound", "smart_call_volume") is None


@pytest.mark.asyncio
async def test_smart_call_volume_hides_when_device_returns_error():
    get_rq = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_READ, [(1, b"")], resp=CMD_SMART_CALL_VOLUME_READ).to_bytes()
    get_resp = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_READ, [(127, HUAWEI_UNSUPPORTED_ERROR)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiSmartCallVolumeHandler()],
        package_response_model={get_rq: [get_resp]},
    )

    await driver.start()

    assert await driver.get_property("sound", "smart_call_volume") is None

    await driver.set_property("sound", "smart_call_volume", "true")

    assert await driver.get_property("sound", "smart_call_volume") is None
    assert driver.package_log == []


@pytest.mark.asyncio
async def test_smart_call_volume_does_not_fake_state_on_write_error():
    get_rq = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_READ, [(1, b"")], resp=CMD_SMART_CALL_VOLUME_READ).to_bytes()
    get_resp = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_READ, [(1, 0)]).to_bytes()
    set_on_rq = HuaweiSppPackage.change_rq(CMD_SMART_CALL_VOLUME_WRITE, [(1, 1)]).to_bytes()
    set_on_resp = HuaweiSppPackage(CMD_SMART_CALL_VOLUME_WRITE, [(127, HUAWEI_UNSUPPORTED_ERROR)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiSmartCallVolumeHandler()],
        package_response_model={
            get_rq: [get_resp],
            set_on_rq: [set_on_resp],
        },
    )

    await driver.start()

    await driver.set_property("sound", "smart_call_volume", "true")

    assert await driver.get_property("sound", "smart_call_volume") == "false"