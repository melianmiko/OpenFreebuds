import struct

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class OfbHuaweiAbstractTapActionHandler(OfbDriverHandlerHuawei):
    def __init__(self, w_in_call=False, options_map: dict[int, str] | None = None,
                 options_call_map: dict[int, str] | None = None, w_read_in_call=False,
                 w_both_ears=False):
        self.prop_prefix = ""
        self.cmd_read = b""
        self.cmd_write = b""

        self.w_in_call = w_in_call
        self.w_read_in_call = w_read_in_call
        self.w_both_ears = w_both_ears
        self._raw_available_codes: list[int] = []
        self._left_code: int | None = None
        self._right_code: int | None = None
        self._options = dict(options_map) if options_map is not None else {
            -1: "tap_action_off",
            1: "tap_action_pause",
            2: "tap_action_next",
            7: "tap_action_prev",
            0: "tap_action_assistant"
        }
        self._options_call = dict(options_call_map) if options_call_map is not None else {
            -1: "tap_action_off",
            0: "tap_action_answer",
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(self.cmd_read, [1, 2]))
        await self.on_package(resp)
        if self.w_read_in_call:
            # Some models store the in-call mapping in parameter 4 and do not
            # return it from the [1, 2] request above. Send the extra query
            # without blocking handler init if the model does not answer it.
            await self.driver.send_package(
                HuaweiSppPackage.change_rq_nowait(self.cmd_read, [(4, b"")])
            )


    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id != self.cmd_read:
            return

        left = package.find_param(1)
        right = package.find_param(2)
        in_call = package.find_param(4)
        available_options = package.find_param(3)
        left_value = None
        right_value = None
        if len(left) == 1:
            self._left_code = int.from_bytes(left, byteorder="big", signed=True)
            left_value = self._options.get(self._left_code, self._left_code)
        if len(right) == 1:
            self._right_code = int.from_bytes(right, byteorder="big", signed=True)
            right_value = self._options.get(self._right_code, self._right_code)

        if self.w_both_ears:
            value = left_value if left_value is not None else right_value
            if value is not None:
                code = self._left_code if left_value is not None else self._right_code
                self._left_code = code
                self._right_code = code
                await self.driver.put_property("action", f"{self.prop_prefix}_left", value)
                await self.driver.put_property("action", f"{self.prop_prefix}_right", value)
        else:
            if left_value is not None:
                await self.driver.put_property("action", f"{self.prop_prefix}_left", left_value)
            if right_value is not None:
                await self.driver.put_property("action", f"{self.prop_prefix}_right", right_value)
        if len(available_options) > 0:
            value = list(struct.unpack(f'{len(available_options)}b', available_options))
            self._raw_available_codes = value
            out = []
            seen = set()
            for v in value:
                act = self._options.get(v, str(v))
                if act not in seen:
                    seen.add(act)
                    out.append(act)
            await self.driver.put_property("action", f"{self.prop_prefix}_options", ",".join(out))
        if len(in_call) == 1 and self.w_in_call:
            value = int.from_bytes(in_call, byteorder="big", signed=True)
            await self.driver.put_property("action", f"{self.prop_prefix}_in_call",
                                           self._options_call.get(value, value))
            await self.driver.put_property("action", f"{self.prop_prefix}_in_call_options",
                                           ",".join(self._options_call.values()))

    def _resolve_action_code(self, p_options: dict[int, str], value) -> int:
        if self._raw_available_codes:
            for code in self._raw_available_codes:
                if p_options.get(code) == value:
                    return code
        for code, act in p_options.items():
            if act == value:
                return code
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except ValueError:
            pass
        raise KeyError(f"Unknown action {value}")

    async def set_property(self, group: str, prop: str, value):
        both_ears = False
        if prop == f"{self.prop_prefix}_left":
            self._left_code = self._resolve_action_code(self._options, value)
            p_type = 1
            code = self._left_code
            both_ears = self.w_both_ears
        elif prop == f"{self.prop_prefix}_right":
            self._right_code = self._resolve_action_code(self._options, value)
            p_type = 2
            code = self._right_code
            both_ears = self.w_both_ears
        elif prop == f"{self.prop_prefix}_in_call":
            code = self._resolve_action_code(self._options_call, value)
            p_type = 4
        else:
            return

        parameters = [(p_type, code)]
        if both_ears:
            self._left_code = code
            self._right_code = code
            parameters = [(1, code), (2, code)]

        pkg = HuaweiSppPackage.change_rq(self.cmd_write, parameters)
        await self.driver.send_package(pkg)
        await self.driver.put_property(group, prop, value)
        if both_ears:
            other = f"{self.prop_prefix}_right" if p_type == 1 else f"{self.prop_prefix}_left"
            await self.driver.put_property(group, other, value)
