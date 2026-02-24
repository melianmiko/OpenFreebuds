from openfreebuds.driver.huawei.constants import CMD_SWIPE_WRITE, CMD_SWIPE_READ
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class OfbHuaweiActionSwipeGestureSplitHandler(OfbDriverHandlerHuawei):
    """
    Swipe config handler

    For devices that support swiping separately left and right.
    """

    handler_id = "gesture_swipe_split"
    commands = [CMD_SWIPE_READ, CMD_SWIPE_WRITE]

    properties = [
        ("action", "swipe_gesture_left"),
        ("action", "swipe_gesture_right"),
    ]

    def __init__(self):
        super().__init__()
        self._options = {
            -1: "tap_action_off",
            0: "tap_action_change_volume",
            1: "tap_action_nextprev",
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_SWIPE_READ, [1, 2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id != CMD_SWIPE_READ:
            return

        left = package.find_param(1)
        right = package.find_param(2)
        if len(left) == 1:
            value = int.from_bytes(left, byteorder="big", signed=True)
            await self.driver.put_property("action", "swipe_gesture_left",
                                           self._options.get(value, value))
        if len(right) == 1:
            value = int.from_bytes(right, byteorder="big", signed=True)
            await self.driver.put_property("action", "swipe_gesture_right",
                                           self._options.get(value, value))
        await self.driver.put_property("action", "swipe_gesture_options", ",".join(self._options.values()))

    async def set_property(self, group: str, prop: str, value):
        if "_left" in prop:
            p_type = 1
        elif "_right" in prop:
            p_type = 2
        else:
            return

        pkg = HuaweiSppPackage.change_rq(CMD_SWIPE_WRITE, [
            (p_type, reverse_dict(self._options)[value]),
        ])
        await self.driver.send_package(pkg)
        await self.driver.put_property(group, prop, value)
