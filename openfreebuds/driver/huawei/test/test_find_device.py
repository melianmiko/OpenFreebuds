import pytest

from openfreebuds.driver.huawei.constants import CMD_HEADSET_SOUND_STATE_READ, CMD_HEADSET_SOUND_STATE_WRITE
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiFindDeviceHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


@pytest.mark.asyncio
async def test_find_device_reads_and_sets_side_state():
    get_left = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(1, 0)], resp=CMD_HEADSET_SOUND_STATE_READ).to_bytes()
    get_right = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(1, 1)], resp=CMD_HEADSET_SOUND_STATE_READ).to_bytes()
    resp_left_idle = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(2, b"\x00\x01")]).to_bytes()
    resp_right_playing = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(2, b"\x01\x00")]).to_bytes()
    resp_left_playing = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(2, b"\x00\x00")]).to_bytes()

    set_left_play = HuaweiSppPackage.change_rq(
        CMD_HEADSET_SOUND_STATE_WRITE,
        [(1, b"\x00\x00")],
    ).to_bytes()
    resp_left_play_ack = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_WRITE, [(2, b"\x00\x00")]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiFindDeviceHandler()],
        package_response_model={
            get_left: [resp_left_idle],
            get_right: [resp_right_playing],
            set_left_play: [resp_left_play_ack],
        },
    )

    await driver.start()
    driver.package_response_model[get_left] = [resp_left_playing]

    assert await driver.get_property("find_device", "left") == "false"
    assert await driver.get_property("find_device", "right") == "true"

    await driver.set_property("find_device", "left", "true")

    assert await driver.get_property("find_device", "left") == "true"
    assert driver.package_log[0] == ("send", set_left_play)
    assert driver.package_log[1] == ("recv", resp_left_play_ack)
    assert driver.package_log[2] == ("send", get_left)
    assert driver.package_log[3] == ("recv", resp_left_playing)


@pytest.mark.asyncio
async def test_find_device_write_ack_does_not_override_followup_read_state():
    get_left = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(1, 0)], resp=CMD_HEADSET_SOUND_STATE_READ).to_bytes()
    get_right = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(1, 1)], resp=CMD_HEADSET_SOUND_STATE_READ).to_bytes()
    resp_left_playing = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(2, b"\x00\x00")]).to_bytes()
    resp_left_idle = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(2, b"\x00\x01")]).to_bytes()
    resp_right_idle = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(2, b"\x01\x01")]).to_bytes()
    set_left_stop = HuaweiSppPackage.change_rq(
        CMD_HEADSET_SOUND_STATE_WRITE,
        [(1, b"\x00\x01")],
    ).to_bytes()
    resp_left_stop_ack = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_WRITE, [(2, b"\x00\x00")]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiFindDeviceHandler()],
        package_response_model={
            get_left: [resp_left_playing],
            get_right: [resp_right_idle],
            set_left_stop: [resp_left_stop_ack],
        },
    )

    await driver.start()
    driver.package_response_model[get_left] = [resp_left_idle]

    assert await driver.get_property("find_device", "left") == "true"

    await driver.set_property("find_device", "left", "false")

    assert await driver.get_property("find_device", "left") == "false"


@pytest.mark.asyncio
async def test_find_device_does_not_fake_state_on_write_error():
    get_left = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(1, 0)], resp=CMD_HEADSET_SOUND_STATE_READ).to_bytes()
    get_right = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(1, 1)], resp=CMD_HEADSET_SOUND_STATE_READ).to_bytes()
    resp_left_idle = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(2, b"\x00\x01")]).to_bytes()
    resp_right_idle = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(2, b"\x01\x01")]).to_bytes()
    set_left_play = HuaweiSppPackage.change_rq(
        CMD_HEADSET_SOUND_STATE_WRITE,
        [(1, b"\x00\x00")],
    ).to_bytes()
    resp_error = HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_WRITE, [(127, b"\x00\x01\x86\xa3")]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiFindDeviceHandler()],
        package_response_model={
            get_left: [resp_left_idle],
            get_right: [resp_right_idle],
            set_left_play: [resp_error],
        },
    )

    await driver.start()

    await driver.set_property("find_device", "left", "true")

    assert await driver.get_property("find_device", "left") == "false"