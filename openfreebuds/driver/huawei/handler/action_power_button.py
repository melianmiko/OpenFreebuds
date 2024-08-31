from openfreebuds.driver.huawei.constants import CMD_DUAL_TAP_READ, CMD_DUAL_TAP_WRITE
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class OfbHuaweiActionsPowerButtonHandler(OfbDriverHandlerHuawei):
    """
    Power button double tap config handler
    """

    handler_id = "gesture_power"
    commands = [CMD_DUAL_TAP_READ, CMD_DUAL_TAP_WRITE]

    properties = [
        ("action", "power_button"),
    ]

    def __init__(self):
        super().__init__()
        self._options = {
            -1: "tap_action_off",
            12: "tap_action_switch_device"
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_DUAL_TAP_READ, [1, 2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id != CMD_DUAL_TAP_READ:
            return

        action = package.find_param(1)
        if len(action) == 1:
            value = int.from_bytes(action, byteorder="big", signed=True)
            await self.driver.put_property("action", "power_button",
                                           self._options.get(value, value))
        await self.driver.put_property("action", "power_button_options", ",".join(self._options.values()))

    async def set_property(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage.change_rq(CMD_DUAL_TAP_WRITE, [
            (1, reverse_dict(self._options)[value]),
            (2, reverse_dict(self._options)[value]),
        ])
        await self.driver.send_package(pkg)
        await self.driver.put_property(group, prop, value)
