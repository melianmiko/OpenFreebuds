"""Tests for HUAWEI FreeClip 2 driver

Based on real device data from:
  - Model: BTFT0027
  - Submodel: BTFT0027-000167
  - Firmware: HarmonyOS 6.1.0.352(F003H003C00)
  - Hardware: HL1SAKM_Ver.A
  - Serial: 74XTQ26430008502
"""

import pytest

from openfreebuds.driver.huawei.driver.per_model.free_clip_2 import OfbDriverHuaweiFreeClip2


@pytest.mark.asyncio
async def test_driver_creation():
    """Test that FreeClip 2 driver can be instantiated with all handlers"""
    d = OfbDriverHuaweiFreeClip2("00:11:22:33:44:55")
    assert len(d.handlers) > 0
    assert d._spp_service_port == 1

    handler_ids = [h.handler_id for h in d.handlers]
    expected_handlers = [
        "device_info",
        "battery",
        "tws_auto_pause",
        "gesture_double",
        "gesture_triple",
        "gesture_long_split",
        "gesture_swipe",
        "config_eq",
        "config_sound_quality",
        "low_latency",
        "tws_in_ear",
        "voice_language",
        "dual_connect",
    ]
    for handler_id in expected_handlers:
        assert handler_id in handler_ids, f"Missing handler: {handler_id}"


@pytest.mark.asyncio
async def test_device_supported():
    """Test that FreeClip 2 is in the device-to-driver map"""
    from openfreebuds.driver import DEVICE_TO_DRIVER_MAP, is_device_supported

    assert "HUAWEI FreeClip 2" in DEVICE_TO_DRIVER_MAP
    assert DEVICE_TO_DRIVER_MAP["HUAWEI FreeClip 2"] == OfbDriverHuaweiFreeClip2
    assert is_device_supported("HUAWEI FreeClip 2") is True
    # Original FreeClip should still be on Pro3 driver
    assert DEVICE_TO_DRIVER_MAP["HUAWEI FreeClip"] is not OfbDriverHuaweiFreeClip2
