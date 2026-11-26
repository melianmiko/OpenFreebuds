from openfreebuds.driver.huawei.constants import CMD_LONG_TAP_SPLIT_READ_BASE, CMD_LONG_TAP_SPLIT_READ_ANC, \
    CMD_LONG_TAP_SPLIT_WRITE_BASE, CMD_LONG_TAP_SPLIT_WRITE_ANC
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class OfbHuaweiActionLongTapSplitHandler(OfbDriverHandlerHuawei):
    """
    Long tap ANC mode cycle setting.

    For devices who store this option in two separate parameters:
    long tap action and preferred modes

    Tested on 4i
    """

    handler_id = "gesture_long_split"
    commands = [
        CMD_LONG_TAP_SPLIT_READ_BASE,
        CMD_LONG_TAP_SPLIT_READ_ANC,
        CMD_LONG_TAP_SPLIT_WRITE_BASE,
        CMD_LONG_TAP_SPLIT_WRITE_ANC,
    ]
    properties = [
        ("action", "long_tap_left"),
        ("action", "long_tap_right"),
        ("action", "long_tap_in_call"),
        ("action", "noise_control_left"),
        ("action", "noise_control_right"),
    ]

    def __init__(self, w_left=True, w_right=False, w_in_call=False, w_anc=True, w_extra_options=False,
                 w_agent_modes=False, options_map: dict[int, str] | None = None):
        self.w_left = w_left
        self.w_right = w_right
        self.w_in_call = w_in_call
        self.w_anc = w_anc
        self.w_agent_modes = w_agent_modes

        self._options_lt = dict(options_map) if options_map is not None else {
            -1: "tap_action_off",
            10: "tap_action_switch_anc"
        }
        if options_map is not None:
            # The caller supplied the exact action set exposed by this model.
            # Do not add options inherited from other product families.
            self.w_agent_modes = False
            w_extra_options = False

        self._options_lt_call = {
            -1: "tap_action_off",
            0: "tap_action_answer"
        }

        self._options_anc = {
            1: "noise_control_off_on",
            2: "noise_control_off_on_aw",
            3: "noise_control_on_aw",
            4: "noise_control_off_aw"
        }

        if w_agent_modes:
            # FreeClip 2 style: only assistant or disabled, no volume/ANC actions.
            # Both earbuds always have an independent long-tap action.
            self.w_left = True
            self.w_right = True
            self._options_lt = {
                -1: "tap_action_off",
                0: "tap_action_assistant"
            }
            self.properties = [*self.properties, ("action", "long_tap_mode")]
        elif w_extra_options:
            self._options_lt[0] = "tap_action_assistant"
            self._options_lt[18] = "tap_action_vol_up"
            self._options_lt[19] = "tap_action_vol_down"

    async def on_init(self):
        # Base request. p4 is the in-call action; ask for it explicitly so
        # devices that do not push it on their own still report a value.
        if self.w_agent_modes:
            params = [1, 2, 9, 10]
        else:
            params = [1, 2]
        if self.w_in_call:
            params.append(4)

        resp = await self.driver.send_package(
            HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_BASE, params)
        )
        await self.on_package(resp)

        # ANC options request
        if self.w_anc:
            resp = await self.driver.send_package(
                HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_ANC, [1, 2])
            )
            await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
        if prop == "long_tap_mode":
            if not self.w_agent_modes:
                return
            # Measured 2026-11-16 with the official App and 0x2B17 readback:
            #   press-to-talk  p9=1, p10=1
            #   continuous conversation  p9=0, p10=0
            # Note: p1=ff,p2=fe in the official config_zaas.json are App-layer
            # 'leave action unchanged' placeholders and must not be written to the device as-is;
            # doing so writes ff/fe to the left/right actions (left off, right invalid) and disables long-press on both ears.
            # So read the current p1/p2 action codes and write them back unchanged; only p9/p10 may change.
            if value not in ("ptt", "hold"):
                return False
            lt_codes = reverse_dict(self._options_lt)
            left_current = await self.driver.get_property("action", "long_tap_left")
            right_current = await self.driver.get_property("action", "long_tap_right")
            # Treat -2/unknown readback as 'off' so an invalid code is not written back
            left_action = lt_codes.get(left_current, -1)
            right_action = lt_codes.get(right_current, -1)
            ptt = value == "ptt"
            pkg = HuaweiSppPackage.change_rq(CMD_LONG_TAP_SPLIT_WRITE_BASE, [
                (1, left_action),
                (2, right_action),
                (9, 1 if ptt else 0),
                (10, 1 if ptt else 0),
            ])
            await self.driver.send_package(pkg)
            await self.driver.put_property(group, prop, value)
            return

        if "_left" in prop:
            p_type = 1
            p_options = self._options_lt
        elif "_right" in prop:
            p_type = 2
            p_options = self._options_lt
        elif "_in_call" in prop:
            p_type = 4
            p_options = self._options_lt_call
        else:
            return

        if prop.startswith("long_tap"):
            # Main action
            pkg = HuaweiSppPackage(CMD_LONG_TAP_SPLIT_WRITE_BASE, [
                (p_type, reverse_dict(p_options)[value]),
            ])
        else:
            # ANC modes
            pkg = HuaweiSppPackage(CMD_LONG_TAP_SPLIT_WRITE_ANC, [
                (p_type, reverse_dict(self._options_anc)[value]),
            ])

        await self.driver.send_package(pkg)
        await self.driver.put_property(group, prop, value)

    async def on_package(self, package: HuaweiSppPackage):
        left = package.find_param(1)
        right = package.find_param(2)
        in_call = package.find_param(4)
        if package.command_id == CMD_LONG_TAP_SPLIT_READ_BASE:
            if len(left) == 1 and self.w_left:
                value = int.from_bytes(left, byteorder="big", signed=True)
                if value < 0:
                    value = -1
                await self.driver.put_property("action", "long_tap_left",
                                               self._options_lt.get(value, value))
            if len(right) == 1 and self.w_right:
                value = int.from_bytes(right, byteorder="big", signed=True)
                if value < 0:
                    value = -1
                await self.driver.put_property("action", "long_tap_right",
                                               self._options_lt.get(value, value))
            if len(in_call) == 1 and self.w_in_call:
                value = int.from_bytes(in_call, byteorder="big", signed=True)
                await self.driver.put_property("action", "long_tap_in_call",
                                               self._options_lt_call.get(value, value))
                await self.driver.put_property("action", "long_tap_in_call_options",
                                               ",".join(self._options_lt_call.values()))
            await self.driver.put_property("action", "long_tap_options", ",".join(self._options_lt.values()))

            if self.w_agent_modes:
                mode_ptt = package.find_param(9)
                mode_hold = package.find_param(10)
                if len(mode_ptt) == 1 and len(mode_hold) == 1:
                    # Official calibration: press-to-talk = 9/10 both 1; continuous conversation = 9/10 both 0.
                    mode = "ptt" if mode_ptt[0] == 1 and mode_hold[0] == 1 else "hold"
                    await self.driver.put_property("action", "long_tap_mode", mode)
                    await self.driver.put_property("action", "long_tap_mode_options", "ptt,hold")
        elif package.command_id == CMD_LONG_TAP_SPLIT_READ_ANC:
            if len(left) == 1:
                value = int.from_bytes(left, byteorder="big", signed=True)
                await self.driver.put_property("action", "noise_control_left",
                                               self._options_anc.get(value, value))
            if len(right) == 1 and self.w_right:
                value = int.from_bytes(right, byteorder="big", signed=True)
                await self.driver.put_property("action", "noise_control_right",
                                               self._options_anc.get(value, value))
            await self.driver.put_property("action", "noise_control_options", ",".join(self._options_anc.values()))
