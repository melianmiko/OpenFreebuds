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

    def __init__(self, w_left=True, w_right=False, w_in_call=False, w_anc=True):
        self.w_left = w_left
        self.w_right = w_right
        self.w_in_call = w_in_call
        self.w_anc = w_anc

        self._options_lt = {
            -1: "tap_action_off",
            10: "tap_action_switch_anc"
        }
        self._options_lt_call = {
            -1: "tap_action_off",
            10: "tap_action_answer"
        }
        self._options_anc = {
            1: "noise_control_off_on",
            2: "noise_control_off_on_aw",
            3: "noise_control_on_aw",
            4: "noise_control_off_aw"
        }

    async def on_init(self):
        # Base request
        resp = await self.driver.send_package(
            HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_BASE, [1, 2])
        )
        await self.on_package(resp)

        # ANC options request
        if self.w_anc:
            resp = await self.driver.send_package(
                HuaweiSppPackage.read_rq(CMD_LONG_TAP_SPLIT_READ_ANC, [1, 2])
            )
            await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
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
                await self.driver.put_property("action", "long_tap_left",
                                               self._options_lt.get(value, value))
            if len(right) == 1 and self.w_right:
                value = int.from_bytes(right, byteorder="big", signed=True)
                await self.driver.put_property("action", "long_tap_right",
                                               self._options_lt.get(value, value))
            if len(in_call) == 1 and self.w_in_call:
                value = int.from_bytes(right, byteorder="big", signed=True)
                await self.driver.put_property("action", "long_tap_in_call",
                                               self._options_lt_call.get(value, value))
                await self.driver.put_property("action", "long_tap_in_call_options",
                                               ",".join(self._options_lt_call.values()))
            await self.driver.put_property("action", "long_tap_options", ",".join(self._options_lt.values()))
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
