"""Spatial audio handler tests (0x2BB4 feature 24).
Protocol based on 2026-11-13 FreeClip 2 nine-state calibration: read 01 01 18 02 00 03 00 -> p2=mode p3=sound field. Mode p2: 0 off / 1 head tracking / 2 fixed. Sound field p3: 0 default / 1 theater / 2 cinema / 3 concert hall (kept when off).
"""

import pytest

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_SPATIAL_AUDIO
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiSpatialAudioHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

READ_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_SPATIAL_AUDIO), (2, b""), (3, b"")]
).to_bytes()


def resp(mode: int, room: int) -> bytes:
    return HuaweiSppPackage.change_rq(
        CMD_MBB_FEATURE, [(1, b"\x18"), (2, bytes([mode])), (3, bytes([room]))]
    ).to_bytes()


def mode_rq(mode: int) -> bytes:
    return HuaweiSppPackage.change_rq(
        CMD_MBB_FEATURE, [(1, MBB_FEATURE_SPATIAL_AUDIO), (2, mode)]
    ).to_bytes()


def room_rq(room: int) -> bytes:
    return HuaweiSppPackage.change_rq(
        CMD_MBB_FEATURE, [(1, MBB_FEATURE_SPATIAL_AUDIO), (3, room)]
    ).to_bytes()


def base_model(mode: int, room: int):
    return {READ_RQ: [resp(mode, room)]}


async def create_driver(model):
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiSpatialAudioHandler()],
        package_response_model=model,
    )
    await driver.start()
    return driver


COMBOS = [
    ("head_tracking", "default", 1, 0),
    ("head_tracking", "theater", 1, 1),
    ("head_tracking", "cinema", 1, 2),
    ("head_tracking", "concert_hall", 1, 3),
    ("fixed", "default", 2, 0),
    ("fixed", "theater", 2, 1),
    ("fixed", "cinema", 2, 2),
    ("fixed", "concert_hall", 2, 3),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode_name,room_name,mode_val,room_val", COMBOS)
async def test_read_combos(mode_name, room_name, mode_val, room_val):
    driver = await create_driver(base_model(mode_val, room_val))
    sound = await driver.get_property("sound", None)
    assert sound["spatial_audio_supported"] == "true"
    assert sound["spatial_audio"] == "true"
    assert sound["spatial_audio_mode"] == mode_name
    assert sound["spatial_audio_room"] == room_name


@pytest.mark.asyncio
async def test_read_off_keeps_room():
    driver = await create_driver(base_model(0, 3))
    sound = await driver.get_property("sound", None)
    assert sound["spatial_audio"] == "false"
    assert sound["spatial_audio_mode"] == "off"
    assert sound["spatial_audio_room"] == "concert_hall"


@pytest.mark.asyncio
async def test_write_mode():
    model = base_model(1, 0)
    model[mode_rq(2)] = [resp(2, 0)]
    driver = await create_driver(model)

    assert await driver.set_property("sound", "spatial_audio_mode", "fixed") is True
    assert await driver.get_property("sound", "spatial_audio_mode") == "fixed"


@pytest.mark.asyncio
async def test_write_room():
    model = base_model(2, 0)
    model[room_rq(3)] = [resp(2, 3)]
    driver = await create_driver(model)

    assert await driver.set_property("sound", "spatial_audio_room", "concert_hall") is True
    assert await driver.get_property("sound", "spatial_audio_room") == "concert_hall"


@pytest.mark.asyncio
async def test_write_toggle_on_from_off():
    model = base_model(0, 2)
    model[mode_rq(1)] = [resp(1, 2)]
    driver = await create_driver(model)

    assert await driver.set_property("sound", "spatial_audio", "true") is True
    sound = await driver.get_property("sound", None)
    assert sound["spatial_audio"] == "true"
    assert sound["spatial_audio_mode"] == "head_tracking"
    assert sound["spatial_audio_room"] == "cinema"


@pytest.mark.asyncio
async def test_write_toggle_off():
    model = base_model(1, 2)
    model[mode_rq(0)] = [resp(0, 2)]
    driver = await create_driver(model)

    assert await driver.set_property("sound", "spatial_audio", "false") is True
    sound = await driver.get_property("sound", None)
    assert sound["spatial_audio"] == "false"
    assert sound["spatial_audio_mode"] == "off"


@pytest.mark.asyncio
async def test_unsupported():
    driver = await create_driver({})

    assert await driver.get_property("sound", "spatial_audio_supported") == "false"
    assert await driver.set_property("sound", "spatial_audio_mode", "fixed") is False