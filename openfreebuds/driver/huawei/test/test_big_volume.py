import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_BIG_VOLUME_NEW_READ,
    CMD_BIG_VOLUME_NEW_WRITE,
    CMD_BIG_VOLUME_READ,
    CMD_BIG_VOLUME_WRITE,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiBigVolumeHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


HUAWEI_UNSUPPORTED_ERROR = b"\x00\x01\x86\xa3"


@pytest.mark.asyncio
async def test_big_volume_uses_new_protocol_when_supported():
    support_rq = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_READ, [(2, b"")], resp=CMD_BIG_VOLUME_NEW_READ).to_bytes()
    support_resp = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_READ, [(2, 1)]).to_bytes()
    state_rq = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_READ, [(1, b"")], resp=CMD_BIG_VOLUME_NEW_READ).to_bytes()
    state_resp = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_READ, [(1, 1)]).to_bytes()
    set_off_rq = HuaweiSppPackage.change_rq(CMD_BIG_VOLUME_NEW_WRITE, [(1, 0)]).to_bytes()
    set_off_resp = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_WRITE, [(1, 0)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiBigVolumeHandler()],
        package_response_model={
            support_rq: [support_resp],
            state_rq: [state_resp],
            set_off_rq: [set_off_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("sound", "big_volume") == "true"

    await driver.set_property("sound", "big_volume", "false")

    assert await driver.get_property("sound", "big_volume") == "false"
    assert driver.package_log[0] == ("send", set_off_rq)


@pytest.mark.asyncio
async def test_big_volume_falls_back_to_legacy_protocol():
    support_rq = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_READ, [(2, b"")], resp=CMD_BIG_VOLUME_NEW_READ).to_bytes()
    support_resp = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_READ, [(2, 0)]).to_bytes()
    state_rq = HuaweiSppPackage(CMD_BIG_VOLUME_READ, [(1, b"")], resp=CMD_BIG_VOLUME_READ).to_bytes()
    state_resp = HuaweiSppPackage(CMD_BIG_VOLUME_READ, [(1, 0)]).to_bytes()
    set_on_rq = HuaweiSppPackage.change_rq(CMD_BIG_VOLUME_WRITE, [(1, 1)]).to_bytes()
    set_on_resp = HuaweiSppPackage(CMD_BIG_VOLUME_WRITE, [(1, 1)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiBigVolumeHandler()],
        package_response_model={
            support_rq: [support_resp],
            state_rq: [state_resp],
            set_on_rq: [set_on_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("sound", "big_volume") == "false"

    await driver.set_property("sound", "big_volume", "true")

    assert await driver.get_property("sound", "big_volume") == "true"
    assert driver.package_log[0] == ("send", set_on_rq)


@pytest.mark.asyncio
async def test_big_volume_hides_when_device_rejects_command():
    support_rq = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_READ, [(2, b"")], resp=CMD_BIG_VOLUME_NEW_READ).to_bytes()
    support_resp = HuaweiSppPackage(CMD_BIG_VOLUME_NEW_READ, [(127, HUAWEI_UNSUPPORTED_ERROR)]).to_bytes()
    state_rq = HuaweiSppPackage(CMD_BIG_VOLUME_READ, [(1, b"")], resp=CMD_BIG_VOLUME_READ).to_bytes()
    state_resp = HuaweiSppPackage(CMD_BIG_VOLUME_READ, [(127, HUAWEI_UNSUPPORTED_ERROR)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiBigVolumeHandler()],
        package_response_model={
            support_rq: [support_resp],
            state_rq: [state_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("sound", "big_volume") is None

    await driver.set_property("sound", "big_volume", "true")

    assert await driver.get_property("sound", "big_volume") is None
    assert driver.package_log == []