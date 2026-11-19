"""Tests for recently added HUAWEI drivers

All of these drivers are derived from the official feature matrix and the
App config resources (config_<productId>.json). Only FreeClip 2 itself has
been verified on real hardware.
"""

import pytest

from openfreebuds.driver import DEVICE_TO_DRIVER_MAP
from openfreebuds.driver.huawei.driver.per_model.buds_5 import OfbDriverHuawei5
from openfreebuds.driver.huawei.driver.per_model.buds_5i import OfbDriverHuawei5I
from openfreebuds.driver.huawei.driver.per_model.buds_6 import OfbDriverHuawei6
from openfreebuds.driver.huawei.driver.per_model.buds_6i import OfbDriverHuawei6I
from openfreebuds.driver.huawei.driver.per_model.buds_7 import OfbDriverHuawei7
from openfreebuds.driver.huawei.driver.per_model.buds_7i import OfbDriverHuawei7I
from openfreebuds.driver.huawei.driver.per_model.buds_neo import OfbDriverHuaweiNeo
from openfreebuds.driver.huawei.driver.per_model.buds_pro import OfbDriverHuaweiPro
from openfreebuds.driver.huawei.driver.per_model.buds_pro_2 import OfbDriverHuaweiPro2
from openfreebuds.driver.huawei.driver.per_model.buds_pro_3 import OfbDriverHuaweiPro3
from openfreebuds.driver.huawei.driver.per_model.buds_pro_4 import OfbDriverHuaweiPro4
from openfreebuds.driver.huawei.driver.per_model.buds_pro_5 import OfbDriverHuaweiPro5
from openfreebuds.driver.huawei.driver.per_model.buds_se_4 import OfbDriverHuaweiSe4
from openfreebuds.driver.huawei.driver.per_model.buds_studio import OfbDriverHuaweiStudio
from openfreebuds.driver.huawei.driver.per_model.free_clip import OfbDriverHuaweiFreeClip
from openfreebuds.driver.huawei.driver.per_model.free_clip_2 import OfbDriverHuaweiFreeClip2
from openfreebuds.driver.huawei.driver.per_model.free_clip_2_s import OfbDriverHuaweiFreeClip2S

COMMON_HANDLERS = [
    "device_info",
    "battery",
    "tws_auto_pause",
    "gesture_double",
    "gesture_long_split",
    "gesture_swipe",
    "config_eq",
    "config_sound_quality",
    "low_latency",
    "tws_in_ear",
    "voice_language",
    "dual_connect",
    "config_head_control",
]


@pytest.mark.parametrize("driver_cls,expected", [
    (OfbDriverHuawei5, [
        "device_info", "battery", "tws_auto_pause",
        "gesture_double", "gesture_triple", "gesture_long_split", "gesture_swipe",
        "config_eq", "config_sound_quality", "low_latency", "tws_in_ear",
        "voice_language", "dual_connect", "anc_global",
    ]),
    (OfbDriverHuawei7, COMMON_HANDLERS + [
        "anc_global", "gesture_triple", "gesture_light_hold",
        "config_spatial_audio", "config_adaptive_volume", "config_box_tone",
        "config_drop_reminder",
    ]),
    (OfbDriverHuaweiNeo, COMMON_HANDLERS + [
        "anc_global", "gesture_triple", "config_spatial_audio", "config_adaptive_volume",
    ]),
    (OfbDriverHuawei7I, COMMON_HANDLERS + [
        "anc_global", "gesture_triple", "config_spatial_audio",
    ]),
    (OfbDriverHuawei6, COMMON_HANDLERS + [
        "gesture_triple", "config_adaptive_volume", "config_box_tone",
        "config_drop_reminder",
    ]),
    (OfbDriverHuaweiFreeClip2S, [
        "device_info", "battery", "tws_auto_pause", "gesture_double", "gesture_triple",
        "gesture_long_split", "gesture_swipe", "config_eq", "config_sound_quality",
        "low_latency", "tws_in_ear", "voice_language", "dual_connect",
        "config_spatial_audio", "config_adaptive_volume", "config_box_tone",
        "config_head_control", "config_drop_reminder",
    ]),
    (OfbDriverHuaweiPro5, ["config_adaptive_volume", "config_spatial_audio",
                           "config_head_control", "config_box_tone",
                           "gesture_light_hold", "gesture_double", "gesture_triple",
                           "gesture_long_split", "gesture_swipe"]),
    (OfbDriverHuaweiPro2, ["device_info", "battery", "anc_global", "config_eq",
                           "gesture_light_hold", "gesture_long_split", "gesture_swipe"]),
    (OfbDriverHuaweiPro3, ["device_info", "battery", "anc_global", "config_eq",
                           "gesture_light_hold", "gesture_long_split", "gesture_swipe",
                           "config_spatial_audio", "config_box_tone"]),
    (OfbDriverHuaweiPro4, ["device_info", "battery", "anc_global", "config_eq",
                           "gesture_light_hold", "gesture_long_split", "gesture_swipe",
                           "gesture_double", "gesture_triple", "config_adaptive_volume",
                           "config_spatial_audio", "config_box_tone", "config_head_control"]),
    (OfbDriverHuaweiFreeClip, ["device_info", "battery", "anc_global", "config_eq",
                               "gesture_double", "gesture_triple",
                               "config_head_control", "config_drop_reminder",
                               "config_box_tone"]),
])
def test_driver_handlers(driver_cls, expected):
    d = driver_cls("00:11:22:33:44:55")
    assert d._spp_service_port == 1
    handler_ids = [h.handler_id for h in d.handlers]
    for handler_id in expected:
        assert handler_id in handler_ids, f"{driver_cls.__name__} missing handler: {handler_id}"


def test_freeclip2_in_call_double_tap_supported():
    d = OfbDriverHuaweiFreeClip2("00:11:33:44:55")
    handler = next(h for h in d.handlers if h.handler_id == "gesture_double")
    assert handler.w_in_call is True
    assert handler.w_read_in_call is True
    assert handler._options_call[0] == "tap_action_answer_end"
    assert handler._options_call[-1] == "tap_action_off"


def _get_handler(driver_cls, handler_id):
    d = driver_cls("00:11:22:33:44:55")
    return next(h for h in d.handlers if h.handler_id == handler_id)


def test_freebuds7_light_hold_and_in_call_double_tap():
    d = OfbDriverHuawei7("00:11:22:33:44:55")
    handler_ids = [h.handler_id for h in d.handlers]
    assert "gesture_light_hold" in handler_ids
    light_hold = _get_handler(OfbDriverHuawei7, "gesture_light_hold")
    assert light_hold.w_light_hold is True
    assert light_hold.w_pinch_hold is True
    double = _get_handler(OfbDriverHuawei7, "gesture_double")
    assert double.w_in_call is True
    assert double.w_read_in_call is True


def test_pro3_gesture_set_replaces_double_tap():
    d = OfbDriverHuaweiPro3("00:11:22:33:44:55")
    handler_ids = [h.handler_id for h in d.handlers]
    assert "gesture_light_hold" in handler_ids
    assert "gesture_double" not in handler_ids
    assert "config_spatial_audio" in handler_ids
    assert "config_box_tone" in handler_ids
    assert _get_handler(OfbDriverHuaweiPro3, "config_box_tone").w_lid_tone is False


@pytest.mark.parametrize("driver_cls,w_lid_tone", [
    (OfbDriverHuaweiPro3, False),
    (OfbDriverHuaweiPro4, False),
    (OfbDriverHuaweiFreeClip, False),
    (OfbDriverHuawei6, True),
    (OfbDriverHuawei7, True),
    (OfbDriverHuaweiPro5, True),
    (OfbDriverHuaweiFreeClip2, True),
    (OfbDriverHuaweiFreeClip2S, True),
])
def test_box_tone_lid_control_scope(driver_cls, w_lid_tone):
    assert _get_handler(driver_cls, "config_box_tone").w_lid_tone is w_lid_tone


def test_neo_has_no_drop_reminder():
    d = OfbDriverHuaweiNeo("00:11:22:33:44:55")
    assert "config_drop_reminder" not in [h.handler_id for h in d.handlers]


def test_pro4_gesture_set():
    d = OfbDriverHuaweiPro4("00:11:22:33:44:55")
    handler_ids = [h.handler_id for h in d.handlers]
    for handler_id in ("gesture_double", "gesture_triple", "gesture_light_hold",
                       "config_adaptive_volume", "config_spatial_audio", "config_box_tone"):
        assert handler_id in handler_ids
    double = _get_handler(OfbDriverHuaweiPro4, "gesture_double")
    assert double.w_in_call is True
    assert double.w_read_in_call is True


def test_freeclip_gesture_set():
    d = OfbDriverHuaweiFreeClip("00:11:22:33:44:55")
    handler_ids = [h.handler_id for h in d.handlers]
    assert "gesture_double" in handler_ids
    assert "gesture_triple" in handler_ids
    assert "config_box_tone" in handler_ids
    for handler_id in ("gesture_light_hold", "gesture_long_split", "gesture_swipe",
                       "config_spatial_audio"):
        assert handler_id not in handler_ids
    double = _get_handler(OfbDriverHuaweiFreeClip, "gesture_double")
    assert double.w_in_call is True
    assert double.w_read_in_call is True
    box_tone = _get_handler(OfbDriverHuaweiFreeClip, "config_box_tone")
    assert box_tone.w_lid_tone is False


def test_freeclip_driver_is_standalone():
    """Clip 1 has its own handler list; it must not inherit Pro 3."""
    assert not issubclass(OfbDriverHuaweiFreeClip, OfbDriverHuaweiPro3)


def test_neo_double_tap_in_call():
    double = _get_handler(OfbDriverHuaweiNeo, "gesture_double")
    assert double.w_in_call is True
    assert double.w_read_in_call is True


@pytest.mark.parametrize("driver_cls", [
    OfbDriverHuawei5,
    OfbDriverHuawei5I,
    OfbDriverHuawei6,
    OfbDriverHuawei6I,
    OfbDriverHuawei7I,
    OfbDriverHuaweiNeo,
    OfbDriverHuaweiSe4,
])
def test_long_tap_in_call_enabled(driver_cls):
    handler = _get_handler(driver_cls, "gesture_long_split")
    assert handler.w_in_call is True


def test_freeclip2_long_tap_has_no_in_call_page():
    """Clip 2's AI-key page has no isInCall field; only double-tap has one."""
    handler = _get_handler(OfbDriverHuaweiFreeClip2, "gesture_long_split")
    assert handler.w_in_call is False


def test_custom_eq_enabled_for_pro2_and_5i():
    for driver_cls in (OfbDriverHuaweiPro2, OfbDriverHuawei5I):
        handler = _get_handler(driver_cls, "config_eq")
        assert handler.w_custom is True


def test_freebuds5_has_no_standalone_spatial_audio():
    """FreeBuds 5 only supports HD spatial audio when connected to a Huawei device; the desktop UI has no standalone control."""
    d = OfbDriverHuawei5("00:11:22:33:44:55")
    handler_ids = [h.handler_id for h in d.handlers]
    assert "config_spatial_audio" not in handler_ids


@pytest.mark.parametrize("device_name,driver_cls", [
    ("HUAWEI FreeBuds 5", OfbDriverHuawei5),
    ("FreeBuds 5", OfbDriverHuawei5),
    ("Honey", OfbDriverHuawei5),
    ("HONEY", OfbDriverHuawei5),
    ("HUAWEI FreeBuds Lipstick 2", OfbDriverHuawei5),
    ("FreeBuds Lipstick 2", OfbDriverHuawei5),
    ("Diva", OfbDriverHuawei5),
    ("DIVA", OfbDriverHuawei5),
    ("HUAWEI FreeBuds 6", OfbDriverHuawei6),
    ("Harper", OfbDriverHuawei6),
    ("HUAWEI FreeBuds 7", OfbDriverHuawei7),
    ("HUAWEI FreeBuds 7i", OfbDriverHuawei7I),
    ("Conch", OfbDriverHuawei7I),
    ("HUAWEI FreeBuds Neo", OfbDriverHuaweiNeo),
    ("HUAWEI FreeClip 2 典藏版", OfbDriverHuaweiFreeClip2S),
    ("HUAWEI FreeClip 2 S", OfbDriverHuaweiFreeClip2S),
])
def test_device_map(device_name, driver_cls):
    assert DEVICE_TO_DRIVER_MAP[device_name] is driver_cls


def test_freebuds5_has_no_spatial_audio():
    d = OfbDriverHuawei5("00:11:22:33:44:55")
    assert "config_spatial_audio" not in [h.handler_id for h in d.handlers]


@pytest.mark.parametrize("driver_cls,expected", [
    (OfbDriverHuawei5, True),
    (OfbDriverHuawei5I, True),
    (OfbDriverHuaweiFreeClip2S, True),
])
def test_find_earbud_default_supported(driver_cls, expected):
    d = driver_cls("00:11:22:33:44:55")
    d._ensure_find_earbud_handler()
    assert d.supports_find_earbud is expected
    assert ("find_earbud" in [h.handler_id for h in d.handlers]) is expected


@pytest.mark.parametrize("driver_cls", [
    OfbDriverHuaweiPro,
    OfbDriverHuaweiStudio,
])
def test_find_earbud_excluded_models(driver_cls):
    d = driver_cls("00:11:22:33:44:55")
    d._ensure_find_earbud_handler()
    assert d.supports_find_earbud is False
    assert "find_earbud" not in [h.handler_id for h in d.handlers]


@pytest.mark.parametrize("driver_cls", sorted(
    {c for c in DEVICE_TO_DRIVER_MAP.values() if hasattr(c, "supports_find_earbud")},
    key=lambda c: c.__name__,
))
def test_find_earbud_matrix_all_huawei_drivers(driver_cls):
    """Official capability matrix: only Pro 1st gen and Studio lack find-earbud; all other models have it."""
    d = driver_cls("00:11:22:33:44:55")
    d._ensure_find_earbud_handler()
    expected = driver_cls not in (OfbDriverHuaweiPro, OfbDriverHuaweiStudio)
    actual = "find_earbud" in [h.handler_id for h in d.handlers]
    assert actual is expected, f"{driver_cls.__name__} find_earbud={actual}, expected={expected}"
