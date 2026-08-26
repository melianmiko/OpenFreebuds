import struct

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class OfbHuaweiAbstractTapActionHandler(OfbDriverHandlerHuawei):
    def __init__(self, w_in_call=False, options_map: dict[int, str] | None = None):
        self.prop_prefix = ""
        self.cmd_read = b""
        self.cmd_write = b""

        self.w_in_call = w_in_call
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
        self._options_call = {
            -1: "tap_action_off",
            0: "tap_action_answer",
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(self.cmd_read, [1, 2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id != self.cmd_read:
            return

        left = package.find_param(1)
        right = package.find_param(2)
        in_call = package.find_param(4)
        available_options = package.find_param(3)
        if len(left) == 1:
            self._left_code = int.from_bytes(left, byteorder="big", signed=True)
            await self.driver.put_property("action", f"{self.prop_prefix}_left",
                                           self._options.get(self._left_code, self._left_code))
        if len(right) == 1:
            self._right_code = int.from_bytes(right, byteorder="big", signed=True)
            await self.driver.put_property("action", f"{self.prop_prefix}_right",
                                           self._options.get(self._right_code, self._right_code))
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
        if prop == f"{self.prop_prefix}_left":
            self._left_code = self._resolve_action_code(self._options, value)
            p_type = 1
            code = self._left_code
        elif prop == f"{self.prop_prefix}_right":
            self._right_code = self._resolve_action_code(self._options, value)
            p_type = 2
            code = self._right_code
        elif prop == f"{self.prop_prefix}_in_call":
            code = self._resolve_action_code(self._options_call, value)
            p_type = 4
        else:
            return

        pkg = HuaweiSppPackage.change_rq(self.cmd_write, [
            (p_type, code),
        ])
        await self.driver.send_package(pkg)
        await self.driver.put_property(group, prop, value)
