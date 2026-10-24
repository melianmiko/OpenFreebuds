"""Tests for features addressed by id through command 2bb4.

Frames are real HUAWEI FreeBuds 7i traffic captured from HUAWEI AI Life.
"""

import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiFeaturesHandler

READ_SPATIAL = bytes.fromhex("5a000a002bb4010118020003009b3f")
READ_HEAD = bytes.fromhex("5a0006002bb401010b289b")
READ_SINGLE_BUD_ANC = bytes.fromhex("5a0008002bb40101050200b389")

RESP_SPATIAL_HEAD_TRACKING = bytes.fromhex("5a000c002bb4010118020101030100a19e")
RESP_HEAD_OFF = bytes.fromhex("5a000f002bb401010b0201000301010401027d3a")
RESP_SINGLE_BUD_ANC_ON = bytes.fromhex("5a0009002bb401010502010152ed")


def _driver(extra_model=None):
    model = {
        READ_SPATIAL: [RESP_SPATIAL_HEAD_TRACKING],
        READ_HEAD: [RESP_HEAD_OFF],
        READ_SINGLE_BUD_ANC: [RESP_SINGLE_BUD_ANC_ON],
        **(extra_model or {}),
    }
    return FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiFeaturesHandler(w_spatial_audio=True, w_head_gestures=True, w_single_bud_anc=True)],
        package_response_model=model,
    )


@pytest.mark.asyncio
async def test_read_all():
    driver = _driver()
    await driver.start()

    assert await driver.get_property("sound", "spatial_audio") == "spatial_head_tracking"
    assert await driver.get_property("sound", "spatial_audio_options") == \
        "spatial_off,spatial_fixed,spatial_head_tracking"
    assert await driver.get_property("sound", "spatial_audio_effect") == "spatial_effect_default"
    assert await driver.get_property("action", "head_gestures") == "false"
    assert await driver.get_property("action", "head_nod") == "tap_action_answer"
    assert await driver.get_property("action", "head_shake") == "tap_action_reject"
    assert await driver.get_property("action", "head_nod_options") == \
        "tap_action_answer,tap_action_reject,tap_action_off"
    assert await driver.get_property("config", "single_bud_anc") == "true"


@pytest.mark.asyncio
async def test_set_spatial_audio():
    set_fixed = bytes.fromhex("5a0009002bb401011802010240af")
    resp_fixed = bytes.fromhex("5a000c002bb40101180201020301003a42")
    set_cinema = bytes.fromhex("5a0009002bb4010118030102779f")
    resp_cinema = bytes.fromhex("5a000c002bb401011802010103010281dc")

    driver = _driver({set_fixed: [resp_fixed], set_cinema: [resp_cinema]})
    await driver.start()

    await driver.set_property("sound", "spatial_audio", "spatial_fixed")
    assert driver.package_log[0] == ("send", set_fixed)
    assert await driver.get_property("sound", "spatial_audio") == "spatial_fixed"

    driver.package_log = []
    await driver.set_property("sound", "spatial_audio_effect", "spatial_effect_cinema")
    assert driver.package_log[0] == ("send", set_cinema)
    assert await driver.get_property("sound", "spatial_audio_effect") == "spatial_effect_cinema"


@pytest.mark.asyncio
async def test_set_head_gestures():
    set_on = bytes.fromhex("5a0009002bb401010b020101f0b7")
    resp_on = bytes.fromhex("5a000f002bb401010b020101030101040102c55b")
    set_nod_reject = bytes.fromhex("5a0009002bb401010b030102f7e4")
    resp_nod_reject = bytes.fromhex("5a000f002bb401010b0201010301020401025e87")

    driver = _driver({set_on: [resp_on], set_nod_reject: [resp_nod_reject]})
    await driver.start()

    await driver.set_property("action", "head_gestures", "true")
    assert driver.package_log[0] == ("send", set_on)
    assert await driver.get_property("action", "head_gestures") == "true"

    driver.package_log = []
    await driver.set_property("action", "head_nod", "tap_action_reject")
    assert driver.package_log[0] == ("send", set_nod_reject)
    assert await driver.get_property("action", "head_nod") == "tap_action_reject"


@pytest.mark.asyncio
async def test_set_single_bud_anc():
    set_off = bytes.fromhex("5a0009002bb401010502010042cc")
    resp_off = bytes.fromhex("5a0009002bb401010502010042cc")

    driver = _driver({set_off: [resp_off]})
    await driver.start()

    await driver.set_property("config", "single_bud_anc", "false")
    assert driver.package_log[0] == ("send", set_off)
    assert await driver.get_property("config", "single_bud_anc") == "false"


@pytest.mark.asyncio
async def test_disabled_features_are_not_read():
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiFeaturesHandler(w_spatial_audio=True)],
        package_response_model={READ_SPATIAL: [RESP_SPATIAL_HEAD_TRACKING]},
    )
    await driver.start()
    assert await driver.get_property("action", "head_gestures") is None
    assert await driver.get_property("config", "single_bud_anc") is None
