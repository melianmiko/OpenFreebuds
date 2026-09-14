import pytest

from openfreebuds.driver import DEVICE_TO_DRIVER_MAP
from openfreebuds.driver.huawei.constants import CMD_DEVICE_TIME, CMD_HEADSET_SOUND_STATE, CMD_LOG_REPORT_RESULT
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.driver.per_model import OfbDriverHuaweiPro5
from openfreebuds.driver.huawei.driver.per_model.buds_pro_5 import (PRO_5_EQ_PRESETS, PRO_5_FEATURE_SWITCHES,
                                                                    PRO_5_LIGHT_LONG_TAP_OPTIONS,
                                                                    PRO_5_LIGHT_TAP_SPECS,
                                                                    PRO_5_LONG_TAP_OPTIONS)
from openfreebuds.driver.huawei.handler import (OfbHuaweiActionLightLongTapHandler, OfbHuaweiActionTripleTapHandler,
                                                OfbHuaweiAncHandler,
                                                OfbHuaweiEqualizerPresetHandler,
                                                OfbHuaweiFindDeviceHandler,
                                                OfbHuaweiFeatureSwitchHandler, OfbHuaweiInfoHandler,
                                                OfbHuaweiLogsHandler, OfbHuaweiPromptToneHandler)
from openfreebuds.driver.huawei.package import HuaweiSppPackage


def test_pro_5_profile_registered():
    assert DEVICE_TO_DRIVER_MAP["HUAWEI FreeBuds Pro 5"] is OfbDriverHuaweiPro5


def test_pro_5_profile_uses_apk_feature_ids():
    driver = OfbDriverHuaweiPro5("")

    assert any(isinstance(handler, OfbHuaweiInfoHandler) for handler in driver.handlers)
    assert OfbHuaweiFeatureSwitchHandler(PRO_5_FEATURE_SWITCHES).features == {
        "adaptive_audio": 2,
        "voice_wakeup": 3,
        "smart_charge": 4,
        "alone_noise": 5,
        "head_control": 11,
        "conversation_awareness": 27,
        "charging_case_gesture": 34,
        "earplug_type": 8,
        "spatial_audio_mode": 24,
        "spatial_audio_room": 24,
        "voice_control": 35,
    }
    assert any(
        isinstance(handler, OfbHuaweiFeatureSwitchHandler)
        and handler.features == OfbHuaweiFeatureSwitchHandler(PRO_5_FEATURE_SWITCHES).features
        for handler in driver.handlers
    )
    assert {handler.handler_id for handler in driver.handlers}.isdisjoint({
        "big_volume",
        "smart_call_volume",
        "left_right_ear_recognition",
    })
    assert any(isinstance(handler, OfbHuaweiPromptToneHandler) for handler in driver.handlers)


def test_pro_5_profile_ignores_apk_system_notifications():
    driver = OfbDriverHuaweiPro5("")

    assert any(
        isinstance(handler, OfbHuaweiLogsHandler)
        and CMD_LOG_REPORT_RESULT in handler.ignore_commands
        and CMD_DEVICE_TIME in handler.ignore_commands
        and CMD_HEADSET_SOUND_STATE in handler.ignore_commands
        for handler in driver.handlers
    )


def test_pro_5_profile_uses_apk_eq_modes():
    driver = OfbDriverHuaweiPro5("")
    eq_handlers = [handler for handler in driver.handlers if isinstance(handler, OfbHuaweiEqualizerPresetHandler)]

    assert len(eq_handlers) == 1
    assert PRO_5_EQ_PRESETS == {
        2: "bass",
        5: "default",
        9: "voice",
        13: "movie",
        14: "game",
        15: "podcast",
        16: "sports",
        17: "ai",
        18: "tchaikovsky_balance",
        19: "tchaikovsky_theatre",
        -55: "classical",
    }
    assert eq_handlers[0].w_custom is True


def test_pro_5_profile_uses_apk_gesture_modes():
    driver = OfbDriverHuaweiPro5("")

    assert PRO_5_LONG_TAP_OPTIONS == {
        -1: "tap_action_off",
        0: "tap_action_assistant",
        10: "tap_action_switch_anc",
        15: "tap_action_short_audio",
    }
    assert PRO_5_LIGHT_LONG_TAP_OPTIONS == {
        -1: "tap_action_off",
        0: "tap_action_assistant",
        1: "tap_action_pause",
        2: "tap_action_next",
        3: "tap_action_switch_anc",
        4: "tap_action_short_audio",
        5: "tap_action_assistant",
        6: "tap_action_switch_anc",
    }
    assert [spec.prop_prefix for spec in PRO_5_LIGHT_TAP_SPECS] == [
        "light_tap_call_once",
        "light_tap_call_twice",
        "light_tap_once",
        "light_tap_twice",
        "light_tap_three",
        "light_long_tap",
    ]
    assert any(isinstance(handler, OfbHuaweiActionTripleTapHandler) for handler in driver.handlers)
    assert any(
        isinstance(handler, OfbHuaweiActionLightLongTapHandler)
        and [spec.prop_prefix for spec in handler.specs] == [spec.prop_prefix for spec in PRO_5_LIGHT_TAP_SPECS]
        for handler in driver.handlers
    )
    assert any(isinstance(handler, OfbHuaweiFindDeviceHandler) for handler in driver.handlers)


@pytest.mark.asyncio
async def test_pro_5_voice_wakeup_reads_live_state_from_param2():
    get_voice_wakeup_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 3), (2, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_voice_wakeup_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 3), (2, b"\x01\x00"), (3, 4)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({"voice_wakeup": PRO_5_FEATURE_SWITCHES["voice_wakeup"]}),
        ],
        package_response_model={get_voice_wakeup_rq: [get_voice_wakeup_resp]},
    )

    await driver.start()

    assert await driver.get_property("features", "voice_wakeup") == "true"


@pytest.mark.asyncio
async def test_pro_5_charging_case_gesture_uses_extended_payload():
    get_charging_case_gesture_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 34), (2, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_charging_case_gesture_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 34), (2, b"\x00\x00\x00\x00")],
    ).to_bytes()
    set_charging_case_gesture_on_rq = HuaweiSppPackage.change_rq(
        b"\x2b\xb4",
        [(1, 34), (2, b"\x01\x00\x00\x00")],
    ).to_bytes()
    set_charging_case_gesture_on_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 34), (2, b"\x01\x00\x00\x00")],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({
                "charging_case_gesture": PRO_5_FEATURE_SWITCHES["charging_case_gesture"],
            }),
        ],
        package_response_model={
            get_charging_case_gesture_rq: [get_charging_case_gesture_resp],
            set_charging_case_gesture_on_rq: [set_charging_case_gesture_on_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("features", "charging_case_gesture") == "false"

    await driver.set_property("features", "charging_case_gesture", "true")

    assert await driver.get_property("features", "charging_case_gesture") == "true"
    assert driver.package_log[0] == ("send", set_charging_case_gesture_on_rq)


@pytest.mark.asyncio
async def test_pro_5_awareness_level_is_mapped_from_device_dump():
    get_anc_rq = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2]).to_bytes()
    get_anc_resp = HuaweiSppPackage(
        b"\x2b\x2a",
        [
            (1, b"\x04\x02"),
            (2, b"\x00"),
        ],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiAncHandler(
                w_cancel_lvl=True,
                w_cancel_dynamic=True,
                w_voice_boost=True,
                awareness_level_options={
                    1: "voice_boost",
                    2: "standard_transparency",
                    4: "adaptive_transparency",
                },
            ),
        ],
        package_response_model={
            get_anc_rq: [get_anc_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("anc", "mode") == "awareness"
    assert await driver.get_property("anc", "level") == "adaptive_transparency"
    assert await driver.get_property("anc", "level_options") == (
        "voice_boost,standard_transparency,adaptive_transparency"
    )


@pytest.mark.asyncio
async def test_unknown_anc_level_is_kept_as_string():
    get_anc_rq = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2]).to_bytes()
    get_anc_resp = HuaweiSppPackage(
        b"\x2b\x2a",
        [
            (1, b"\x04\x02"),
            (2, b"\x00"),
        ],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
        ],
        package_response_model={
            get_anc_rq: [get_anc_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("anc", "level") == "unknown_4"


@pytest.mark.asyncio
async def test_pro_5_adaptive_awareness_level_uses_apk_payload():
    get_anc_rq = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2]).to_bytes()
    get_anc_resp = HuaweiSppPackage(
        b"\x2b\x2a",
        [
            (1, b"\x04\x02"),
            (2, b"\x05"),
        ],
    ).to_bytes()
    set_awareness_level_rq = HuaweiSppPackage.change_rq(
        b"\x2b\x04",
        [
            (1, b"\x02\x04"),
            (3, 1),
            (4, 5),
        ],
    ).to_bytes()
    set_awareness_level_resp = HuaweiSppPackage(
        b"\x2b\x04",
        [(2, 0)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiAncHandler(
                w_cancel_lvl=True,
                w_cancel_dynamic=True,
                w_voice_boost=True,
                awareness_level_options={
                    1: "voice_boost",
                    2: "standard_transparency",
                    4: "adaptive_transparency",
                },
            ),
        ],
        package_response_model={
            get_anc_rq: [get_anc_resp],
            set_awareness_level_rq: [set_awareness_level_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("anc", "awareness_level") == "5"
    assert await driver.get_property("anc", "awareness_level_min") == "0"
    assert await driver.get_property("anc", "awareness_level_max") == "10"

    await driver.set_property("anc", "awareness_level", "5")

    assert driver.package_log[0] == ("send", set_awareness_level_rq)