import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.driver.per_model.buds_pro_5 import PRO_5_LIGHT_LONG_TAP_OPTIONS
from openfreebuds.driver.huawei.handler import (OfbHuaweiActionDoubleTapHandler,
                                                HuaweiLightTapSpec,
                                                OfbHuaweiActionLightLongTapHandler,
                                                OfbHuaweiActionLongTapSplitHandler,
                                                OfbHuaweiActionSwipeGestureHandler)
from openfreebuds.driver.huawei.package import HuaweiSppPackage


HUAWEI_UNSUPPORTED_ERROR = b"\x00\x01\x86\xa3"


@pytest.mark.asyncio
async def test_swipe_tap():
    # Real device traffic dumps
    get_swipe = bytes.fromhex("5a0007002b1f01000200328a")
    resp_swipe = bytes.fromhex("5a000a002b1f010100030200ff9e79")
    set_swipe_off = bytes.fromhex("5a0009002b1e0101ff0201ff9d9b")
    resp_swipe_off = bytes.fromhex("5a0006002b1e030100754d")

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionSwipeGestureHandler()
        ],
        package_response_model={
            get_swipe: [resp_swipe],
            set_swipe_off: [resp_swipe_off],
        }
    )

    await driver.start()
    assert await driver.get_property("action", "swipe_gesture") == "tap_action_change_volume"

    # Write left
    driver.package_log = []
    await driver.set_property("action", "swipe_gesture", "tap_action_off")
    assert await driver.get_property("action", "swipe_gesture") == "tap_action_off"
    rq0, rq1 = driver.package_log
    assert rq0 == ('send', set_swipe_off)
    assert rq1 == ('recv', resp_swipe_off)


@pytest.mark.asyncio
async def test_double_tap():
    # Real device traffic dumps
    get_double_tap = bytes.fromhex("5a000700012001000200e897")
    resp_double_tap = bytes.fromhex("5a0017000120010101020102030501070200ff0401ff060200ffcf60")
    set_left_to_next = bytes.fromhex("5a000600011f01010203c1")
    resp_left_to_next = bytes.fromhex("5a000600011f0301004de3")
    set_in_call_on = bytes.fromhex("5a000600011f040100c873")
    resp_in_call_on = bytes.fromhex("5a000600011f060100a613")

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionDoubleTapHandler(w_in_call=True)
        ],
        package_response_model={
            get_double_tap: [resp_double_tap],
            set_left_to_next: [resp_left_to_next],
            set_in_call_on: [resp_in_call_on],
        }
    )

    await driver.start()

    # Read
    await driver.send_package(HuaweiSppPackage.from_bytes(get_double_tap))
    assert await driver.get_property("action", "double_tap_left") == "tap_action_pause"
    assert await driver.get_property("action", "double_tap_right") == "tap_action_next"
    assert await driver.get_property("action", "double_tap_in_call") == "tap_action_off"

    # Write left
    driver.package_log = []
    await driver.set_property("action", "double_tap_left", "tap_action_next")
    assert await driver.get_property("action", "double_tap_left") == "tap_action_next"
    rq0, rq1 = driver.package_log
    assert rq0 == ('send', set_left_to_next)
    assert rq1 == ('recv', resp_left_to_next)

    # Write in-call
    driver.package_log = []
    await driver.set_property("action", "double_tap_in_call", "tap_action_answer")
    assert await driver.get_property("action", "double_tap_in_call") == "tap_action_answer"
    assert driver.package_log[0] == ('send', set_in_call_on)
    assert driver.package_log[1] == ('recv', resp_in_call_on)


@pytest.mark.asyncio
async def test_long_tap():
    # Real device dumps
    get_long_tap_base = bytes.fromhex("5a0007002b170100020030a7")
    resp_long_tap_base = bytes.fromhex("5a001f002b1701010a02010a030d000102030405060708090a0e0f040100060200ff520c")
    get_long_tap_anc = bytes.fromhex("5a0007002b1901000200ff0f")
    resp_long_tap_anc = bytes.fromhex("5a0015002b19010102020102030a0102030405060708090a7d45")
    set_anc_off_awr = bytes.fromhex("5a0006002b180201042560")
    resp_anc_off_awr = bytes.fromhex("5a0006002b180301027296")

    # Surrogate
    set_long_tap_off = bytes.fromhex("5a0006002b160101ff801e")
    resp_long_tap_off = bytes.fromhex("5a0006002b16030100f08e")

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionLongTapSplitHandler(w_right=True, w_in_call=True)
        ],
        package_response_model={
            get_long_tap_base: [resp_long_tap_base],
            get_long_tap_anc: [resp_long_tap_anc],
            set_anc_off_awr: [resp_anc_off_awr],
            set_long_tap_off: [resp_long_tap_off],
        }
    )

    await driver.start()
    assert await driver.get_property("action", "long_tap_left") == "tap_action_switch_anc"
    assert await driver.get_property("action", "long_tap_right") == "tap_action_switch_anc"
    # assert await driver.get_property("action", "long_tap_in_call") == "tap_action_answer"
    assert await driver.get_property("action", "noise_control_left") == "noise_control_off_on_aw"
    assert await driver.get_property("action", "noise_control_right") == "noise_control_off_on_aw"

    # Write anc
    driver.package_log = []
    await driver.set_property("action", "noise_control_right", "noise_control_off_aw")
    assert await driver.get_property("action", "noise_control_right") == "noise_control_off_aw"
    assert driver.package_log[0] == ('send', set_anc_off_awr)
    assert driver.package_log[1] == ('recv', resp_anc_off_awr)

    # Write long-tap
    driver.package_log = []
    await driver.set_property("action", "long_tap_left", "tap_action_off")
    assert await driver.get_property("action", "long_tap_left") == "tap_action_off"
    assert driver.package_log[0] == ('send', set_long_tap_off)
    assert driver.package_log[1] == ('recv', resp_long_tap_off)


@pytest.mark.asyncio
async def test_light_long_tap():
    get_light_long_tap = HuaweiSppPackage(
        b"\x2b\x93",
        [(1, 3), (2, 0)],
        resp=b"\x2b\x93",
    ).to_bytes()
    resp_light_long_tap = HuaweiSppPackage(
        b"\x2b\x93",
        [(1, 3), (2, 0), (3, -1), (4, -1), (5, b"\x00\x01\x02\x03\x04\xff")],
    ).to_bytes()
    set_right_to_off = HuaweiSppPackage.change_rq(
        b"\x2b\x92",
        [(1, 3), (2, 0), (4, -1)],
    ).to_bytes()
    resp_right_to_off = HuaweiSppPackage(
        b"\x2b\x92",
        [(1, 3), (2, 0), (5, 0)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionLightLongTapHandler(options=PRO_5_LIGHT_LONG_TAP_OPTIONS),
        ],
        package_response_model={
            get_light_long_tap: [resp_light_long_tap],
            set_right_to_off: [resp_right_to_off],
        },
    )

    await driver.start()

    assert await driver.get_property("action", "light_long_tap_left") == "tap_action_off"
    assert await driver.get_property("action", "light_long_tap_right") == "tap_action_off"
    assert await driver.get_property("action", "light_long_tap_options") == \
        "tap_action_off,tap_action_assistant,tap_action_pause,tap_action_next,tap_action_switch_anc,tap_action_short_audio"

    await driver.set_property("action", "light_long_tap_right", "tap_action_off")

    assert await driver.get_property("action", "light_long_tap_right") == "tap_action_off"
    assert driver.package_log[0] == ("send", set_right_to_off)
    assert driver.package_log[1] == ("recv", resp_right_to_off)
    assert driver.package_log[2] == ("send", get_light_long_tap)
    assert driver.package_log[3] == ("recv", resp_light_long_tap)


@pytest.mark.asyncio
async def test_light_long_tap_maps_legacy_live_values():
    get_light_long_tap = HuaweiSppPackage(
        b"\x2b\x93",
        [(1, 3), (2, 0)],
        resp=b"\x2b\x93",
    ).to_bytes()
    resp_light_long_tap = HuaweiSppPackage(
        b"\x2b\x93",
        [(1, 3), (2, 0), (3, 6), (4, 6), (5, b"\x00\x01\x02\x03\x04\xff")],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionLightLongTapHandler(options=PRO_5_LIGHT_LONG_TAP_OPTIONS),
        ],
        package_response_model={get_light_long_tap: [resp_light_long_tap]},
    )

    await driver.start()

    assert await driver.get_property("action", "light_long_tap_left") == "tap_action_switch_anc"
    assert await driver.get_property("action", "light_long_tap_right") == "tap_action_switch_anc"
    assert await driver.get_property("action", "light_long_tap_options") == \
        "tap_action_off,tap_action_assistant,tap_action_pause,tap_action_next,tap_action_switch_anc,tap_action_short_audio"


@pytest.mark.asyncio
async def test_light_long_tap_does_not_fake_state_on_write_error():
    get_light_long_tap = HuaweiSppPackage(
        b"\x2b\x93",
        [(1, 3), (2, 0)],
        resp=b"\x2b\x93",
    ).to_bytes()
    resp_light_long_tap = HuaweiSppPackage(
        b"\x2b\x93",
        [(1, 3), (2, 0), (3, -1), (4, -1), (5, b"\x00\x01\x02\x03\x04\xff")],
    ).to_bytes()
    set_left_to_assistant = HuaweiSppPackage.change_rq(
        b"\x2b\x92",
        [(1, 3), (2, 0), (3, 0)],
    ).to_bytes()
    resp_write_error = HuaweiSppPackage(
        b"\x2b\x92",
        [(127, HUAWEI_UNSUPPORTED_ERROR)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionLightLongTapHandler(options=PRO_5_LIGHT_LONG_TAP_OPTIONS),
        ],
        package_response_model={
            get_light_long_tap: [resp_light_long_tap],
            set_left_to_assistant: [resp_write_error],
        },
    )

    await driver.start()

    await driver.set_property("action", "light_long_tap_left", "tap_action_assistant")

    assert await driver.get_property("action", "light_long_tap_left") == "tap_action_off"
    assert driver.package_log[0] == ("send", set_left_to_assistant)
    assert driver.package_log[1] == ("recv", resp_write_error)


@pytest.mark.asyncio
async def test_light_tap_shared_pro5_pages():
    get_pinch_once = HuaweiSppPackage(
        b"\x2b\x93",
        [(1, 0), (2, 2)],
        resp=b"\x2b\x93",
    ).to_bytes()
    resp_pinch_once = HuaweiSppPackage(
        b"\x2b\x93",
        [(1, 0), (2, 2), (3, 2), (4, 2), (5, b"\x02\xff")],
    ).to_bytes()
    set_pinch_once_off = HuaweiSppPackage.change_rq(
        b"\x2b\x92",
        [(1, 0), (2, 2), (3, -1), (4, -1)],
    ).to_bytes()
    resp_pinch_once_off = HuaweiSppPackage(
        b"\x2b\x92",
        [(1, 0), (2, 2), (3, -1), (4, -1), (5, 0)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionLightLongTapHandler(specs=[
                HuaweiLightTapSpec("light_tap_once", 0, 2, shared=True, w_right=False, options={
                    -1: "tap_action_off",
                    2: "tap_action_pause",
                }),
            ]),
        ],
        package_response_model={
            get_pinch_once: [resp_pinch_once],
            set_pinch_once_off: [resp_pinch_once_off],
        },
    )

    await driver.start()

    assert await driver.get_property("action", "light_tap_once") == "tap_action_pause"
    assert await driver.get_property("action", "light_tap_once_options") == "tap_action_off,tap_action_pause"

    await driver.set_property("action", "light_tap_once", "tap_action_off")

    assert await driver.get_property("action", "light_tap_once") == "tap_action_off"
    assert driver.package_log[0] == ("send", set_pinch_once_off)
    assert driver.package_log[1] == ("recv", resp_pinch_once_off)
