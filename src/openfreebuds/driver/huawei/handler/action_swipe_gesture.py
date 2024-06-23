from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class FbHuaweiActionSwipeGestureHandler(FbDriverHandlerHuawei):
    """
    Power button double tap config handler
    """

    handler_id = "gesture_swipe"
    commands = [b"\x2b\x1f"]
    ignore_commands = [b"\x2b\x1e"]

    properties = [
        ("action", "swipe_gesture"),
    ]

    def __init__(self):
        super().__init__()
        self._options = {
            -1: "tap_action_off",
            0: "tap_action_change_volume",
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\x1f", [1, 2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        action = package.find_param(1)
        if len(action) == 1:
            value = int.from_bytes(action, byteorder="big", signed=True)
            await self.driver.put_property("action", "swipe_gesture",
                                     self._options.get(value, value))
        await self.driver.put_property("action", "swipe_gesture_options", ",".join(self._options.values()))

    async def set_property(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage.change_rq(b"\x2b\x1e", [
            (1, reverse_dict(self._options)[value]),
            (2, reverse_dict(self._options)[value]),
        ])
        resp = await self.driver.send_package(pkg)
        if resp.find_param(2)[0] == 0:
            await self.driver.put_property(group, prop, value)
