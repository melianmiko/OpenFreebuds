import struct

from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class FbHuaweiAbstractTapActionHandler(FbDriverHandlerHuawei):
    def __init__(self, w_in_call=False):
        self.prop_prefix = ""
        self.cmd_read = b""
        self.cmd_write = b""

        self.w_in_call = w_in_call
        self._options = {
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
            value = int.from_bytes(left, byteorder="big", signed=True)
            await self.driver.put_property("action", f"{self.prop_prefix}_left",
                                           self._options.get(value, value))
        if len(right) == 1:
            value = int.from_bytes(right, byteorder="big", signed=True)
            await self.driver.put_property("action", f"{self.prop_prefix}_right",
                                           self._options.get(value, value))
        if len(available_options) > 0:
            value = list(struct.unpack(f'{len(available_options)}b', available_options))
            out = []
            for v in value:
                out.append(str(v) if v not in self._options else self._options[v])
            await self.driver.put_property("action", f"{self.prop_prefix}_options", ",".join(out))
        if len(in_call) == 1 and self.w_in_call:
            value = int.from_bytes(in_call, byteorder="big", signed=True)
            await self.driver.put_property("action", f"{self.prop_prefix}_in_call",
                                           self._options_call.get(value, value))
            await self.driver.put_property("action", f"{self.prop_prefix}_in_call_options",
                                           ",".join(self._options_call.values()))

    async def set_property(self, group: str, prop: str, value):
        if prop == f"{self.prop_prefix}_left":
            p_type = 1
            p_options = self._options
        elif prop == f"{self.prop_prefix}_right":
            p_type = 2
            p_options = self._options
        elif prop == f"{self.prop_prefix}_in_call":
            p_type = 4
            p_options = self._options_call
        else:
            return

        pkg = HuaweiSppPackage.change_rq(self.cmd_write, [
            (p_type, reverse_dict(p_options)[value]),
        ])
        await self.driver.send_package(pkg)
        await self.driver.put_property(group, prop, value)
