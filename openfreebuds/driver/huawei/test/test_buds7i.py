"""Tests for HUAWEI FreeBuds 7i driver

Responses are real device traffic captured from HUAWEI AI Life:
  - Model: T0025/T0025L
  - Firmware: HarmonyOS 6.1.0.230(F001H003C90)
  - Hardware: HL2ORCMR
"""

import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.driver.per_model.buds_7i import OfbDriverHuawei7I
from openfreebuds.driver.huawei.handler import OfbHuaweiAncHandler, OfbHuaweiEqualizerPresetHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


def test_driver_creation():
    d = OfbDriverHuawei7I("00:11:22:33:44:55")
    assert d._spp_service_port == 1

    handler_ids = [h.handler_id for h in d.handlers]
    for handler_id in [
        "device_info",
        "tws_in_ear",
        "battery",
        "anc_global",
        "gesture_double",
        "gesture_triple",
        "gesture_long_split",
        "gesture_swipe",
        "tws_auto_pause",
        "config_sound_quality",
        "low_latency",
        "config_eq",
        "dual_connect",
        "features",
    ]:
        assert handler_id in handler_ids, f"Missing handler: {handler_id}"


def test_device_supported():
    from openfreebuds.driver import DEVICE_TO_DRIVER_MAP, is_device_supported

    assert DEVICE_TO_DRIVER_MAP["HUAWEI FreeBuds 7i"] == OfbDriverHuawei7I
    assert is_device_supported("HUAWEI FreeBuds 7i") is True


def _anc_handler():
    return [h for h in OfbDriverHuawei7I("").handlers if isinstance(h, OfbHuaweiAncHandler)][0]


@pytest.mark.asyncio
async def test_anc_awareness_voice_boost():
    get_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2]).to_bytes()
    resp_awareness_normal = bytes.fromhex("5a0007002b2a010202025311")
    resp_awareness_voice = bytes.fromhex("5a0007002b2a010201020642")
    set_voice_boost = bytes.fromhex("5a0007002b0401020201a46e")
    resp_set = bytes.fromhex("5a0006002b040201003171")

    model = {get_anc: [resp_awareness_normal]}
    driver = FbDriverHuaweiGenericFixture(handlers=[_anc_handler()], package_response_model=model)
    await driver.start()

    assert await driver.get_property("anc", "mode") == "awareness"
    assert await driver.get_property("anc", "level") == "normal"
    assert await driver.get_property("anc", "level_options") == "voice_boost,normal"

    model[set_voice_boost] = [resp_set]
    model[get_anc] = [resp_awareness_voice]
    driver.package_log = []
    await driver.set_property("anc", "level", "voice_boost")
    assert driver.package_log[0] == ("send", set_voice_boost)
    assert await driver.get_property("anc", "level") == "voice_boost"


@pytest.mark.asyncio
async def test_anc_cancellation_levels():
    get_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2]).to_bytes()
    resp_dynamic = bytes.fromhex("5a0007002b2a010203015043")
    resp_ultra = bytes.fromhex("5a0007002b2a010202016372")
    set_ultra = bytes.fromhex("5a0007002b0401020102c15e")
    resp_set = bytes.fromhex("5a0006002b040201003171")

    model = {get_anc: [resp_dynamic]}
    driver = FbDriverHuaweiGenericFixture(handlers=[_anc_handler()], package_response_model=model)
    await driver.start()

    assert await driver.get_property("anc", "mode") == "cancellation"
    assert await driver.get_property("anc", "level") == "dynamic"

    model[set_ultra] = [resp_set]
    model[get_anc] = [resp_ultra]
    driver.package_log = []
    await driver.set_property("anc", "level", "ultra")
    assert driver.package_log[0] == ("send", set_ultra)
    assert await driver.get_property("anc", "level") == "ultra"


@pytest.mark.asyncio
async def test_equalizer_builtin_preset():
    eq = [h for h in OfbDriverHuawei7I("").handlers if isinstance(h, OfbHuaweiEqualizerPresetHandler)][0]
    get_eq = HuaweiSppPackage.read_rq(b"\x2b\x4a", [1, 2, 3, 4, 5, 6, 7, 8]).to_bytes()
    resp_hi_fi_live = HuaweiSppPackage(b"\x2b\x4a", [
        (1, b"\x01"), (2, b"\xc9"), (3, bytes.fromhex("01020309")), (4, b"\x01"), (8, b""),
    ]).to_bytes()
    set_bass = HuaweiSppPackage(b"\x2b\x49", [(1, 2)]).to_bytes()
    resp_set = bytes.fromhex("5a0009002b497f04000186a0b3c6")
    resp_bass = HuaweiSppPackage(b"\x2b\x4a", [
        (1, b"\x01"), (2, b"\x02"), (3, bytes.fromhex("01020309")), (4, b"\x01"), (8, b""),
    ]).to_bytes()

    model = {get_eq: [resp_hi_fi_live]}
    driver = FbDriverHuaweiGenericFixture(handlers=[eq], package_response_model=model)
    await driver.start()
    assert await driver.get_property("sound", "equalizer_preset") == "equalizer_preset_hi_fi_live"

    model[set_bass] = [resp_set]
    model[get_eq] = [resp_bass]
    await driver.set_property("sound", "equalizer_preset", "equalizer_preset_hardbass")
    assert await driver.get_property("sound", "equalizer_preset") == "equalizer_preset_hardbass"


@pytest.mark.asyncio
async def test_equalizer_fake_built_in_preset_label():
    # The 7i ignores (never answers) 2b49 writes whose label is longer than 24 bytes.
    # HUAWEI AI Life labels the Symphony / Hi-Fi Live presets with their id in decimal.
    eq = [h for h in OfbDriverHuawei7I("").handlers if isinstance(h, OfbHuaweiEqualizerPresetHandler)][0]
    get_eq = HuaweiSppPackage.read_rq(b"\x2b\x4a", [1, 2, 3, 4, 5, 6, 7, 8]).to_bytes()
    resp_bass = HuaweiSppPackage(b"\x2b\x4a", [
        (1, b"\x01"), (2, b"\x02"), (3, bytes.fromhex("01020309")), (4, b"\x01"), (8, b""),
    ]).to_bytes()
    set_symphony = HuaweiSppPackage(b"\x2b\x49", [
        (1, b"\xc8"), (2, 10), (3, bytes.fromhex("0f0f0afb0f190ffb322d")), (4, b"200"), (5, 1),
    ]).to_bytes()
    resp_set = bytes.fromhex("5a0009002b497f04000186a0b3c6")
    resp_symphony = HuaweiSppPackage(b"\x2b\x4a", [
        (1, b"\x01"), (2, b"\xc8"), (3, bytes.fromhex("01020309")), (4, b"\x01"), (8, b""),
    ]).to_bytes()

    model = {get_eq: [resp_bass]}
    driver = FbDriverHuaweiGenericFixture(handlers=[eq], package_response_model=model)
    await driver.start()

    model[set_symphony] = [resp_set]
    model[get_eq] = [resp_symphony]
    await driver.set_property("sound", "equalizer_preset", "equalizer_preset_symphony")
    assert ("send", set_symphony) in driver.package_log
    assert await driver.get_property("sound", "equalizer_preset") == "equalizer_preset_symphony"


def test_equalizer_custom_label_is_truncated():
    from openfreebuds.driver.huawei.handler.config_equalizer import _build_payload

    payload = dict(_build_payload(100, "A very long custom preset name", b"\x00" * 10, 1))
    assert payload[4] == b"A very long custom prese"
    # Multibyte characters must not be cut in half
    payload = dict(_build_payload(100, "ñ" * 13, b"\x00" * 10, 1))
    assert payload[4] == ("ñ" * 12).encode("utf8")


@pytest.mark.asyncio
async def test_in_ear_state():
    from openfreebuds.driver.huawei.handler import OfbHuaweiStateInEarHandler

    handler = [h for h in OfbDriverHuawei7I("").handlers if isinstance(h, OfbHuaweiStateInEarHandler)][0]
    get_state = HuaweiSppPackage.read_rq(b"\x2b\x25", [1, 2]).to_bytes()
    resp_both_out = bytes.fromhex("5a000f002b25010100020100030100040100363f")
    both_in = bytes.fromhex("5a000f002b25010101020101030100040100e11b")
    right_out = bytes.fromhex("5a000f002b25010101020100030100040100597a")

    driver = FbDriverHuaweiGenericFixture(handlers=[handler], package_response_model={
        get_state: [resp_both_out],
    })
    await driver.start()
    assert await driver.get_property("state", "in_ear") == "false"

    await driver._handle_raw_pkg(both_in)
    assert await driver.get_property("state", "in_ear") == "true"

    await driver._handle_raw_pkg(right_out)
    assert await driver.get_property("state", "in_ear") == "false"
