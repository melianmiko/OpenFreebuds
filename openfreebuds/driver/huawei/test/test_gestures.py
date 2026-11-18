import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_DUAL_TAP_READ,
    CMD_DUAL_TAP_WRITE,
    CMD_LIGHT_HOLD_READ,
    CMD_LIGHT_HOLD_WRITE,
    CMD_LONG_TAP_SPLIT_READ_BASE,
    CMD_LONG_TAP_SPLIT_WRITE_BASE,
    CMD_SWIPE_WRITE,
    CMD_TRIPLE_TAP_READ,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import (OfbHuaweiActionDoubleTapHandler,
                                                OfbHuaweiActionLightHoldHandler,
                                                OfbHuaweiActionLongTapSplitHandler,
                                                OfbHuaweiActionSwipeGestureHandler,
                                                OfbHuaweiActionTripleTapHandler)
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.driver.huawei.utils import crc16_xmodem


def _response(cmd: bytes, params: list[tuple[int, bytes | int]]) -> bytes:
    """Build a device response packet (recompute CRC)."""
    data = bytearray(HuaweiSppPackage.change_rq(cmd, params).to_bytes())
    data[-2:] = crc16_xmodem(data[:-2])
    return bytes(data)


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
async def test_swipe_tap_split_by_side():
    get_swipe = bytes.fromhex("5a0007002b1f01000200328a")
    resp_swipe = bytes.fromhex("5a000a002b1f010100030200ff9e79")
    ack = _response(CMD_SWIPE_WRITE, [])

    set_left_off = HuaweiSppPackage.change_rq(CMD_SWIPE_WRITE, [(1, -1)]).to_bytes()
    set_right_off = HuaweiSppPackage.change_rq(CMD_SWIPE_WRITE, [(2, -1)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiActionSwipeGestureHandler()],
        package_response_model={
            get_swipe: [resp_swipe],
            set_left_off: [ack],
            set_right_off: [ack],
        }
    )

    await driver.start()
    assert await driver.get_property("action", "swipe_gesture_left") == "tap_action_change_volume"
    assert await driver.get_property("action", "swipe_gesture_right") == "tap_action_change_volume"

    driver.package_log = []
    await driver.set_property("action", "swipe_gesture_left", "tap_action_off")
    assert await driver.get_property("action", "swipe_gesture_left") == "tap_action_off"
    assert await driver.get_property("action", "swipe_gesture_right") == "tap_action_change_volume"
    assert driver.package_log[0] == ('send', set_left_off)

    driver.package_log = []
    await driver.set_property("action", "swipe_gesture_right", "tap_action_off")
    assert await driver.get_property("action", "swipe_gesture_right") == "tap_action_off"
    assert await driver.get_property("action", "swipe_gesture_left") == "tap_action_off"
    assert driver.package_log[0] == ('send', set_right_off)


@pytest.mark.asyncio
async def test_long_tap_mode_keeps_ear_actions():
    read_rq = HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_BASE, [1, 2, 9, 10]).to_bytes()
    read_resp = _response(CMD_LONG_TAP_SPLIT_READ_BASE,
                          [(1, b"\x00"), (2, b"\x00"), (9, b"\x00"), (10, b"\x00")])
    mode_ptt = HuaweiSppPackage.change_rq(CMD_LONG_TAP_SPLIT_WRITE_BASE,
                                          [(1, 0), (2, 0),
                                           (9, 1), (10, 1)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiActionLongTapSplitHandler(w_agent_modes=True, w_anc=False)],
        package_response_model={
            read_rq: [read_resp],
            mode_ptt: [_response(CMD_LONG_TAP_SPLIT_WRITE_BASE, [])],
        }
    )

    await driver.start()
    assert await driver.get_property("action", "long_tap_left") == "tap_action_assistant"
    assert await driver.get_property("action", "long_tap_right") == "tap_action_assistant"
    assert await driver.get_property("action", "long_tap_mode") == "hold"

    driver.package_log = []
    await driver.set_property("action", "long_tap_mode", "ptt")
    assert await driver.get_property("action", "long_tap_mode") == "ptt"
    # Switching modes must preserve the current left/right actions and change only p9/p10 (official: both 1 or both 0)
    assert await driver.get_property("action", "long_tap_left") == "tap_action_assistant"
    assert await driver.get_property("action", "long_tap_right") == "tap_action_assistant"
    assert driver.package_log[0] == ('send', mode_ptt)


@pytest.mark.asyncio
async def test_freeclip2_long_tap_function_payload():
    """FreeClip 2 official long-press actions: per-ear P1/P2 values 00=assistant, FF=off."""
    read_rq = HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_BASE, [1, 2, 9, 10]).to_bytes()
    read_resp = _response(CMD_LONG_TAP_SPLIT_READ_BASE,
                          [(1, b"\x00"), (2, b"\xfe"), (9, b"\x00"), (10, b"\x00")])
    set_left_off = HuaweiSppPackage.change_rq(CMD_LONG_TAP_SPLIT_WRITE_BASE,
                                              [(1, b"\xff")]).to_bytes()
    set_right_on = HuaweiSppPackage.change_rq(CMD_LONG_TAP_SPLIT_WRITE_BASE,
                                              [(2, b"\x00")]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiActionLongTapSplitHandler(w_agent_modes=True, w_anc=False)],
        package_response_model={
            read_rq: [read_resp],
            set_left_off: [_response(CMD_LONG_TAP_SPLIT_WRITE_BASE, [])],
            set_right_on: [_response(CMD_LONG_TAP_SPLIT_WRITE_BASE, [])],
        }
    )

    await driver.start()
    assert await driver.get_property("action", "long_tap_left") == "tap_action_assistant"
    assert await driver.get_property("action", "long_tap_right") == "tap_action_off"
    assert await driver.get_property("action", "long_tap_mode") == "hold"

    await driver.set_property("action", "long_tap_left", "tap_action_off")
    assert driver.package_log[0] == ('send', set_left_off)
    assert await driver.get_property("action", "long_tap_left") == "tap_action_off"
    assert await driver.get_property("action", "long_tap_right") == "tap_action_off"

    driver.package_log = []
    await driver.set_property("action", "long_tap_right", "tap_action_assistant")
    assert driver.package_log[0] == ('send', set_right_on)
    assert await driver.get_property("action", "long_tap_right") == "tap_action_assistant"
    assert await driver.get_property("action", "long_tap_left") == "tap_action_off"


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
async def test_freeclip2_in_call_double_tap():
    """FreeClip 2 reads p4 separately and exposes answer/end or disabled."""
    main_rq = HuaweiSppPackage.read_rq(CMD_DUAL_TAP_READ, [1, 2]).to_bytes()
    call_rq = HuaweiSppPackage.read_rq(CMD_DUAL_TAP_READ, [4]).to_bytes()
    main_resp = _response(CMD_DUAL_TAP_READ, [
        (1, b"\x02"),
        (2, b"\x07"),
        (3, b"\x01\x02\x07\x00\xff"),
    ])
    call_resp = _response(CMD_DUAL_TAP_READ, [(4, b"\x00")])
    call_off = HuaweiSppPackage.change_rq(CMD_DUAL_TAP_WRITE, [(4, -1)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiActionDoubleTapHandler(
                w_in_call=True, w_read_in_call=True,
                options_call_map={
                    0: "tap_action_answer_end",
                    -1: "tap_action_off",
                },
            ),
        ],
        package_response_model={
            main_rq: [main_resp],
            call_rq: [call_resp],
            call_off: [_response(CMD_DUAL_TAP_WRITE, [])],
        },
    )

    await driver.start()
    assert await driver.get_property("action", "double_tap_left") == "tap_action_next"
    assert await driver.get_property("action", "double_tap_right") == "tap_action_prev"
    assert await driver.get_property("action", "double_tap_in_call") == "tap_action_answer_end"
    assert await driver.get_property("action", "double_tap_in_call_options") == \
        "tap_action_answer_end,tap_action_off"

    driver.package_log = []
    await driver.set_property("action", "double_tap_in_call", "tap_action_off")
    assert driver.package_log[0] == ('send', call_off)
    assert await driver.get_property("action", "double_tap_in_call") == "tap_action_off"


@pytest.mark.asyncio
async def test_long_tap():
    # Real device dumps
    get_long_tap_base = HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_BASE, [1, 2, 4]).to_bytes()
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
    assert await driver.get_property("action", "long_tap_in_call") == "tap_action_answer"
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
async def test_long_tap_in_call_reads_p4_not_right():
    """p1 != p2 != p4: only p4 is the in-call action."""
    read_rq = HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_BASE, [1, 2, 4]).to_bytes()
    read_resp = _response(CMD_LONG_TAP_SPLIT_READ_BASE, [
        (1, b"\x0a"),
        (2, b"\x0b"),
        (4, b"\x00"),
    ])

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiActionLongTapSplitHandler(w_in_call=True, w_anc=False)],
        package_response_model={read_rq: [read_resp]},
    )

    await driver.start()
    assert await driver.get_property("action", "long_tap_in_call") == "tap_action_answer"

    # on_init must request p4 explicitly, not rely on an unsolicited report.
    handler = driver.handlers[0]
    driver.package_log = []
    await handler.on_init()
    assert driver.package_log[0] == ('send', read_rq)
    assert await driver.get_property("action", "long_tap_in_call") == "tap_action_answer"


@pytest.mark.asyncio
async def test_long_tap_in_call_write_uses_p4():
    read_rq = HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_BASE, [1, 2, 4]).to_bytes()
    read_resp = _response(CMD_LONG_TAP_SPLIT_READ_BASE, [
        (1, b"\x0a"),
        (2, b"\x0b"),
        (4, b"\x00"),
    ])
    set_in_call_off = HuaweiSppPackage.change_rq(CMD_LONG_TAP_SPLIT_WRITE_BASE, [(4, -1)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiActionLongTapSplitHandler(w_in_call=True, w_anc=False)],
        package_response_model={
            read_rq: [read_resp],
            set_in_call_off: [_response(CMD_LONG_TAP_SPLIT_WRITE_BASE, [])],
        },
    )

    await driver.start()
    driver.package_log = []
    await driver.set_property("action", "long_tap_in_call", "tap_action_off")
    assert driver.package_log[0] == ('send', set_in_call_off)
    assert await driver.get_property("action", "long_tap_in_call") == "tap_action_off"


@pytest.mark.asyncio
async def test_light_hold_pinch_rows():
    """FreeBuds Pro 5 pinch actions and their official value set."""
    reads = {}
    for p1, p2, code in [(0, 1, 0), (0, 2, 2), (1, 1, 1), (1, 2, 4), (2, 2, 3)]:
        rq = HuaweiSppPackage.change_rq(CMD_LIGHT_HOLD_READ, [(1, p1), (2, p2)]).to_bytes()
        reads[rq] = [_response(CMD_LIGHT_HOLD_READ,
                               [(1, p1), (2, p2), (3, code), (4, code)])]

    set_once_off = HuaweiSppPackage.change_rq(CMD_LIGHT_HOLD_WRITE,
                                              [(1, 0), (2, 2), (3, -1), (4, -1)]).to_bytes()
    reads[set_once_off] = [_response(CMD_LIGHT_HOLD_WRITE, [])]

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiActionLightHoldHandler(w_light_hold=True, w_pinch_hold=False)],
        package_response_model=reads,
    )

    await driver.start()
    assert await driver.get_property("action", "light_hold_once_in_call") == "tap_action_answer_end"
    assert await driver.get_property("action", "light_hold_once") == "tap_action_pause"
    assert await driver.get_property("action", "light_hold_twice_in_call") == "tap_action_reject"
    assert await driver.get_property("action", "light_hold_twice") == "tap_action_next"
    assert await driver.get_property("action", "light_hold_three_times") == "tap_action_prev"
    assert await driver.get_property("action", "light_hold_once_options") == "tap_action_pause,tap_action_off"

    driver.package_log = []
    await driver.set_property("action", "light_hold_once", "tap_action_off")
    assert await driver.get_property("action", "light_hold_once") == "tap_action_off"
    assert driver.package_log[0] == ('send', set_once_off)


@pytest.mark.asyncio
async def test_light_hold_pinch_hold_per_ear():
    """Pinch & hold is stored per ear; the official write touches only one side."""
    read_rq = HuaweiSppPackage.change_rq(CMD_LIGHT_HOLD_READ, [(1, 3), (2, 0)]).to_bytes()
    resp = _response(CMD_LIGHT_HOLD_READ, [(1, 3), (2, 0), (3, 6), (4, 5)])
    set_left_off = HuaweiSppPackage.change_rq(CMD_LIGHT_HOLD_WRITE,
                                              [(1, 3), (2, 0), (3, -1)]).to_bytes()
    set_right_assistant = HuaweiSppPackage.change_rq(CMD_LIGHT_HOLD_WRITE,
                                                     [(1, 3), (2, 0), (4, 5)]).to_bytes()
    ack = _response(CMD_LIGHT_HOLD_WRITE, [])

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiActionLightHoldHandler(w_light_hold=False, w_pinch_hold=True)],
        package_response_model={
            read_rq: [resp],
            set_left_off: [ack],
            set_right_assistant: [ack],
        },
    )

    await driver.start()
    assert await driver.get_property("action", "pinch_hold_left") == "tap_action_noise_control"
    assert await driver.get_property("action", "pinch_hold_right") == "tap_action_assistant"
    assert await driver.get_property("action", "pinch_hold_options") == \
        "tap_action_assistant,tap_action_noise_control,tap_action_off"

    driver.package_log = []
    await driver.set_property("action", "pinch_hold_left", "tap_action_off")
    assert driver.package_log[0] == ('send', set_left_off)
    assert await driver.get_property("action", "pinch_hold_right") == "tap_action_assistant"

    driver.package_log = []
    await driver.set_property("action", "pinch_hold_right", "tap_action_assistant")
    assert driver.package_log[0] == ('send', set_right_assistant)


@pytest.mark.asyncio
async def test_freebuds_pro_5_tap_and_long_press_options():
    """Pro 5 tap/long-press pages use the exact official value sets."""
    double_main_rq = HuaweiSppPackage.read_rq(CMD_DUAL_TAP_READ, [1, 2]).to_bytes()
    double_call_rq = HuaweiSppPackage.read_rq(CMD_DUAL_TAP_READ, [4]).to_bytes()
    double_main_resp = _response(CMD_DUAL_TAP_READ,
                                 [(1, b"\x01"), (2, b"\x01"), (3, b"\x01\xff")])
    double_call_resp = _response(CMD_DUAL_TAP_READ, [(4, b"\x00")])
    double_write_off = HuaweiSppPackage.change_rq(CMD_DUAL_TAP_WRITE,
                                                  [(1, -1), (2, -1)]).to_bytes()

    triple_rq = HuaweiSppPackage.read_rq(CMD_TRIPLE_TAP_READ, [1, 2]).to_bytes()
    triple_resp = _response(CMD_TRIPLE_TAP_READ,
                            [(1, b"\x02"), (2, b"\x07"), (3, b"\x02\x07\xff")])

    long_rq = HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_BASE, [1, 2]).to_bytes()
    long_resp = _response(CMD_LONG_TAP_SPLIT_READ_BASE, [(1, b"\x00"), (2, b"\x0a")])

    handlers = [
        OfbHuaweiActionDoubleTapHandler(
            w_in_call=True, w_read_in_call=True, w_both_ears=True,
            options_map={1: "tap_action_pause", -1: "tap_action_off"},
            options_call_map={0: "tap_action_answer_end", -1: "tap_action_off"},
        ),
        OfbHuaweiActionTripleTapHandler(options_map={
            2: "tap_action_next",
            7: "tap_action_prev",
            -1: "tap_action_off",
        }),
        OfbHuaweiActionLongTapSplitHandler(
            w_right=True, w_anc=False,
            options_map={
                0: "tap_action_assistant",
                10: "tap_action_switch_anc",
                -1: "tap_action_off",
            },
        ),
    ]
    driver = FbDriverHuaweiGenericFixture(
        handlers=handlers,
        package_response_model={
            double_main_rq: [double_main_resp],
            double_call_rq: [double_call_resp],
            double_write_off: [_response(CMD_DUAL_TAP_WRITE, [])],
            triple_rq: [triple_resp],
            long_rq: [long_resp],
        },
    )

    await driver.start()
    assert await driver.get_property("action", "double_tap_left") == "tap_action_pause"
    assert await driver.get_property("action", "double_tap_right") == "tap_action_pause"
    assert await driver.get_property("action", "double_tap_options") == \
        "tap_action_pause,tap_action_off"
    assert await driver.get_property("action", "double_tap_in_call") == "tap_action_answer_end"
    assert await driver.get_property("action", "double_tap_in_call_options") == \
        "tap_action_answer_end,tap_action_off"
    assert await driver.get_property("action", "triple_tap_options") == \
        "tap_action_next,tap_action_prev,tap_action_off"
    assert await driver.get_property("action", "long_tap_left") == "tap_action_assistant"
    assert await driver.get_property("action", "long_tap_right") == "tap_action_switch_anc"
    assert await driver.get_property("action", "long_tap_options") == \
        "tap_action_assistant,tap_action_switch_anc,tap_action_off"

    driver.package_log = []
    await driver.set_property("action", "double_tap_left", "tap_action_off")
    assert driver.package_log[0] == ('send', double_write_off)
    assert await driver.get_property("action", "double_tap_left") == "tap_action_off"
    assert await driver.get_property("action", "double_tap_right") == "tap_action_off"
