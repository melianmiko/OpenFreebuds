"""Tests for recently added HUAWEI drivers

All of these drivers are derived from the official feature matrix and the
App config resources (config_<productId>.json). Only FreeClip 2 itself has
been verified on real hardware.
"""

import pytest

from openfreebuds.driver import DEVICE_TO_DRIVER_MAP
from openfreebuds.driver.huawei.driver.per_model.buds_6 import OfbDriverHuawei6
from openfreebuds.driver.huawei.driver.per_model.buds_7 import OfbDriverHuawei7
from openfreebuds.driver.huawei.driver.per_model.buds_7i import OfbDriverHuawei7I
from openfreebuds.driver.huawei.driver.per_model.buds_neo import OfbDriverHuaweiNeo
from openfreebuds.driver.huawei.driver.per_model.buds_pro_5 import OfbDriverHuaweiPro5
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
    (OfbDriverHuawei7, COMMON_HANDLERS + [
        "anc_global", "gesture_triple",
        "config_spatial_audio", "config_adaptive_volume", "config_box_tone",
    ]),
    (OfbDriverHuaweiNeo, COMMON_HANDLERS + [
        "anc_global", "gesture_triple", "config_spatial_audio", "config_adaptive_volume",
    ]),
    (OfbDriverHuawei7I, COMMON_HANDLERS + [
        "anc_global", "gesture_triple", "config_spatial_audio",
    ]),
    (OfbDriverHuawei6, COMMON_HANDLERS + [
        "gesture_triple", "config_adaptive_volume", "config_box_tone",
    ]),
    (OfbDriverHuaweiFreeClip2S, [
        "device_info", "battery", "tws_auto_pause", "gesture_double", "gesture_triple",
        "gesture_long_split", "gesture_swipe", "config_eq", "config_sound_quality",
        "low_latency", "tws_in_ear", "voice_language", "dual_connect",
        "config_spatial_audio", "config_adaptive_volume", "config_box_tone",
        "config_head_control",
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


@pytest.mark.parametrize("device_name,driver_cls", [
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
