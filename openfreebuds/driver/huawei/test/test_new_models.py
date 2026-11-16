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
from openfreebuds.driver.huawei.driver.per_model.buds_7 import OfbDriverHuawei7
from openfreebuds.driver.huawei.driver.per_model.buds_7i import OfbDriverHuawei7I
from openfreebuds.driver.huawei.driver.per_model.buds_neo import OfbDriverHuaweiNeo
from openfreebuds.driver.huawei.driver.per_model.buds_pro import OfbDriverHuaweiPro
from openfreebuds.driver.huawei.driver.per_model.buds_pro_5 import OfbDriverHuaweiPro5
from openfreebuds.driver.huawei.driver.per_model.buds_studio import OfbDriverHuaweiStudio
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
        "anc_global", "gesture_triple",
        "config_spatial_audio", "config_adaptive_volume", "config_box_tone",
        "config_drop_reminder",
    ]),
    (OfbDriverHuaweiNeo, COMMON_HANDLERS + [
        "anc_global", "gesture_triple", "config_spatial_audio", "config_adaptive_volume",
        "config_drop_reminder",
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
                           "config_head_control", "config_box_tone"]),
])
def test_driver_handlers(driver_cls, expected):
    d = driver_cls("00:11:22:33:44:55")
    assert d._spp_service_port == 1
    handler_ids = [h.handler_id for h in d.handlers]
    for handler_id in expected:
        assert handler_id in handler_ids, f"{driver_cls.__name__} missing handler: {handler_id}"


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
