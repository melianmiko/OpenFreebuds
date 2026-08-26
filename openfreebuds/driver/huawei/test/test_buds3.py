import pytest

from openfreebuds.driver.huawei.driver.per_model.buds_3 import OfbDriverHuawei3
from openfreebuds.driver import DEVICE_TO_DRIVER_MAP, is_device_supported


@pytest.mark.asyncio
async def test_driver_creation():
    d = OfbDriverHuawei3("D0:05:E4:12:55:09")
    assert len(d.handlers) > 0
    assert d._spp_service_port == 1

    handler_ids = [h.handler_id for h in d.handlers]
    expected_handlers = [
        "drop_logs",
        "device_info",
        "tws_in_ear",
        "battery",
        "gesture_double",
        "voice_language",
    ]
    for handler_id in expected_handlers:
        assert handler_id in handler_ids, f"Missing handler: {handler_id}"


@pytest.mark.asyncio
async def test_buds3_double_tap():
    from openfreebuds.driver.huawei.driver.per_model.buds_3 import FREEBUDS_3_DOUBLE_TAP_OPTIONS
    from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
    from openfreebuds.driver.huawei.handler import OfbHuaweiActionDoubleTapHandler
    from openfreebuds.driver.huawei.package import HuaweiSppPackage

    # FreeBuds 3 traffic dumps: 0120 returns left=0 (assistant), right=3 (switch_anc), options=[0, 1, 3, 4, -1]
    get_double_tap = HuaweiSppPackage.read_rq(b"\x01\x20", [1, 2])
    resp_double_tap = HuaweiSppPackage(b"\x01\x20", [(1, b"\x00"), (2, b"\x03"), (3, b"\x00\x01\x03\x04\xff")])
    set_right_to_next = HuaweiSppPackage.change_rq(b"\x01\x1f", [(2, 4)])
    resp_right_to_next = HuaweiSppPackage(b"\x01\x1f", [(3, b"\x00")])

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionDoubleTapHandler(options_map=FREEBUDS_3_DOUBLE_TAP_OPTIONS)
        ],
        package_response_model={
            get_double_tap.to_bytes(): [resp_double_tap.to_bytes()],
            set_right_to_next.to_bytes(): [resp_right_to_next.to_bytes()],
        }
    )

    await driver.start()
    assert await driver.get_property("action", "double_tap_left") == "tap_action_assistant"
    assert await driver.get_property("action", "double_tap_right") == "tap_action_switch_anc"
    assert await driver.get_property("action", "double_tap_options") == "tap_action_assistant,tap_action_pause,tap_action_switch_anc,tap_action_next,tap_action_off"

    # Write right to next track (should resolve to 4)
    await driver.set_property("action", "double_tap_right", "tap_action_next")
    assert await driver.get_property("action", "double_tap_right") == "tap_action_next"
    assert driver.package_log[0] == ('send', set_right_to_next.to_bytes())

