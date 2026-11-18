from openfreebuds.driver.huawei.constants import CMD_SWIPE_WRITE, CMD_SWIPE_READ
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class OfbHuaweiActionSwipeGestureHandler(OfbDriverHandlerHuawei):
    """
    Power button double tap config handler
    """

    handler_id = "gesture_swipe"
    commands = [CMD_SWIPE_READ, CMD_SWIPE_WRITE]

    properties = [
        ("action", "swipe_gesture"),
        ("action", "swipe_gesture_left"),
        ("action", "swipe_gesture_right"),
    ]

    def __init__(self, options_map: dict[int, str] | None = None):
        super().__init__()
        self._options = dict(options_map) if options_map is not None else {
            -1: "tap_action_off",
            0: "tap_action_change_volume",
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_SWIPE_READ, [1, 2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id != CMD_SWIPE_READ:
            return

        left = package.find_param(1)
        right = package.find_param(2)
        left_decoded = None
        if len(left) == 1:
            value = int.from_bytes(left, byteorder="big", signed=True)
            left_decoded = self._options.get(value, value)
            await self.driver.put_property("action", "swipe_gesture_left", left_decoded)
            # Legacy property kept for compatibility; reports the left-ear value
            await self.driver.put_property("action", "swipe_gesture", left_decoded)
        if len(right) == 1:
            value = int.from_bytes(right, byteorder="big", signed=True)
            decoded = self._options.get(value, value)
            await self.driver.put_property("action", "swipe_gesture_right", decoded)
        elif left_decoded is not None:
            # Some firmware only returns p1 when both sides share the same value; show that value for the right ear so per-side controls stay visible
            await self.driver.put_property("action", "swipe_gesture_right", left_decoded)
        await self.driver.put_property("action", "swipe_gesture_options", ",".join(self._options.values()))

    async def set_property(self, group: str, prop: str, value):
        code = reverse_dict(self._options)[value]
        if prop == "swipe_gesture_left":
            pkg = HuaweiSppPackage.change_rq(CMD_SWIPE_WRITE, [(1, code)])
        elif prop == "swipe_gesture_right":
            pkg = HuaweiSppPackage.change_rq(CMD_SWIPE_WRITE, [(2, code)])
        else:
            # Legacy property compatibility: write both ears when per-side values are not used
            pkg = HuaweiSppPackage.change_rq(CMD_SWIPE_WRITE, [
                (1, code),
                (2, code),
            ])
        await self.driver.send_package(pkg)
        await self.driver.put_property(group, prop, value)
        if prop in ("swipe_gesture_left", "swipe_gesture_right"):
            await self.driver.put_property("action", "swipe_gesture", value)
