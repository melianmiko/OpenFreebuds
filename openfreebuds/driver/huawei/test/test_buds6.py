"""Tests for HUAWEI FreeBuds 6 driver

Verified against real hardware:
  - Bluetooth name: HUAWEI FreeBuds 6
  - Device model: BTFT0020
  - Firmware: HarmonyOS 6.1.0.358(F003H003C90)
  - Hardware: HR1H6MR_Ver.A
  - SDP: Serial Port (0x1101) on RFCOMM channel 1
  - PnP ID: vendor 0x027D, product 0x4114
"""

import pytest

from openfreebuds.driver.huawei.driver.per_model.buds_6 import OfbDriverHuawei6


@pytest.mark.asyncio
async def test_driver_creation():
    """Test that FreeBuds 6 driver can be instantiated with all handlers"""
    d = OfbDriverHuawei6("00:11:22:33:44:55")
    assert len(d.handlers) > 0
    assert d._spp_service_port == 1

    handler_ids = [h.handler_id for h in d.handlers]
    expected_handlers = [
        "device_info",
        "battery",
        "tws_in_ear",
        "tws_auto_pause",
        "anc_global",
        "gesture_double",
        "gesture_triple",
        "gesture_long_split",
        "gesture_swipe",
        "config_eq",
        "config_sound_quality",
        "voice_language",
        "dual_connect",
    ]
    for handler_id in expected_handlers:
        assert handler_id in handler_ids, f"Missing handler: {handler_id}"


@pytest.mark.asyncio
async def test_device_supported():
    """Test that FreeBuds 6 is in the device-to-driver map"""
    from openfreebuds.driver import DEVICE_TO_DRIVER_MAP, is_device_supported
    from openfreebuds.driver.huawei.driver.per_model.buds_6i import OfbDriverHuawei6I

    assert "HUAWEI FreeBuds 6" in DEVICE_TO_DRIVER_MAP
    assert DEVICE_TO_DRIVER_MAP["HUAWEI FreeBuds 6"] == OfbDriverHuawei6
    assert is_device_supported("HUAWEI FreeBuds 6") is True
    # FreeBuds 6i must keep its own driver
    assert DEVICE_TO_DRIVER_MAP["HUAWEI FreeBuds 6i"] == OfbDriverHuawei6I
