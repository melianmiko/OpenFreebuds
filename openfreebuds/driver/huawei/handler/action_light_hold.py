from dataclasses import dataclass

from openfreebuds.driver.huawei.constants import CMD_LIGHT_HOLD_READ, CMD_LIGHT_HOLD_WRITE
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


@dataclass(frozen=True)
class _LightHoldRow:
    prop: str
    p1: int
    p2: int
    options: dict[int, str]
    separate: bool = False


class OfbHuaweiActionLightHoldHandler(OfbDriverHandlerHuawei):
    """Pinch (light hold) and pinch-and-hold settings for FreeBuds Pro 5.

    The official touchsetting config uses the same command pair for both
    gestures:

    * ``0x2B93`` read / ``0x2B92`` write
    * ``p1`` is the gesture type (0 pinch once, 1 pinch twice,
      2 pinch three times, 3 pinch & hold)
    * ``p2`` is the scene (1 in call, 2 outside a call, 0 for pinch & hold)

    Pinch once/twice/three times are written to both ears (p3/p4) and exposed
    as one control. Pinch & hold is per-ear (p3 left, p4 right), matching the
    official config.
    """

    handler_id = "gesture_light_hold"
    commands = [CMD_LIGHT_HOLD_READ, CMD_LIGHT_HOLD_WRITE]
    properties = [
        ("action", "light_hold_once"),
        ("action", "light_hold_once_in_call"),
        ("action", "light_hold_twice"),
        ("action", "light_hold_twice_in_call"),
        ("action", "light_hold_three_times"),
        ("action", "pinch_hold_left"),
        ("action", "pinch_hold_right"),
    ]

    _PINCH_HOLD_OPTIONS = {
        5: "tap_action_assistant",
        6: "tap_action_noise_control",
        -1: "tap_action_off",
    }

    def __init__(self, w_light_hold=True, w_pinch_hold=False):
        self.w_light_hold = w_light_hold
        self.w_pinch_hold = w_pinch_hold

        self._rows: list[_LightHoldRow] = []
        if w_light_hold:
            self._rows.extend([
                _LightHoldRow("light_hold_once_in_call", 0, 1, {
                    0: "tap_action_answer_end",
                    -1: "tap_action_off",
                }),
                _LightHoldRow("light_hold_once", 0, 2, {
                    2: "tap_action_pause",
                    -1: "tap_action_off",
                }),
                _LightHoldRow("light_hold_twice_in_call", 1, 1, {
                    1: "tap_action_reject",
                    -1: "tap_action_off",
                }),
                _LightHoldRow("light_hold_twice", 1, 2, {
                    4: "tap_action_next",
                    -1: "tap_action_off",
                }),
                _LightHoldRow("light_hold_three_times", 2, 2, {
                    3: "tap_action_prev",
                    -1: "tap_action_off",
                }),
            ])
        if w_pinch_hold:
            self._rows.append(_LightHoldRow(
                "pinch_hold", 3, 0, self._PINCH_HOLD_OPTIONS, separate=True,
            ))

    async def on_init(self):
        for row in self._rows:
            resp = await self.driver.send_package(
                HuaweiSppPackage.change_rq(CMD_LIGHT_HOLD_READ, [
                    (1, row.p1),
                    (2, row.p2),
                ])
            )
            await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id != CMD_LIGHT_HOLD_READ:
            return

        p1 = package.find_param(1)
        p2 = package.find_param(2)
        if len(p1) != 1 or len(p2) != 1:
            return

        row = self._find_row(int.from_bytes(p1, byteorder="big"), int.from_bytes(p2, byteorder="big"))
        if row is None:
            return

        left = package.find_param(3)
        right = package.find_param(4)
        if row.separate:
            if len(left) == 1:
                code = int.from_bytes(left, byteorder="big", signed=True)
                await self.driver.put_property("action", f"{row.prop}_left",
                                               row.options.get(code, code))
            if len(right) == 1:
                code = int.from_bytes(right, byteorder="big", signed=True)
                await self.driver.put_property("action", f"{row.prop}_right",
                                               row.options.get(code, code))
        else:
            # Both ears share the same value for pinch once/twice/three times.
            code_bytes = left if len(left) == 1 else right
            if len(code_bytes) == 1:
                code = int.from_bytes(code_bytes, byteorder="big", signed=True)
                await self.driver.put_property("action", row.prop,
                                               row.options.get(code, code))

        await self.driver.put_property("action", f"{row.prop}_options",
                                       ",".join(row.options.values()))

    async def set_property(self, group: str, prop: str, value):
        row, side = self._find_property(prop)
        if row is None:
            return

        code = reverse_dict(row.options)[value]
        params = [(1, row.p1), (2, row.p2)]
        if row.separate:
            params.append((3 if side == "left" else 4, code))
        else:
            # Official config writes p3 and p4 together for the shared pinch
            # gestures, so both ears stay in sync.
            params.extend([(3, code), (4, code)])

        pkg = HuaweiSppPackage.change_rq(CMD_LIGHT_HOLD_WRITE, params)
        await self.driver.send_package(pkg)
        await self.driver.put_property(group, prop, value)

    def _find_row(self, p1: int, p2: int) -> _LightHoldRow | None:
        for row in self._rows:
            if row.p1 == p1 and row.p2 == p2:
                return row
        return None

    def _find_property(self, prop: str) -> tuple[_LightHoldRow | None, str | None]:
        for row in self._rows:
            if row.separate:
                if prop == f"{row.prop}_left":
                    return row, "left"
                if prop == f"{row.prop}_right":
                    return row, "right"
            elif prop == row.prop:
                return row, None
        return None, None
