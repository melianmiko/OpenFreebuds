from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class FbHuaweiActionLongTapHandler(FbDriverHandlerHuawei):
    """
    Long tap config handler

    For devices without separate left/right long tap setup,
    and without split prop conf.
    """

    handler_id = "gesture_long"
    commands = [b"\x2b\x17"]
    ignore_commands = [b"\x2b\x16"]
    properties = [
        ("action", "long_tap"),
    ]

    def __init__(self):
        super().__init__()
        self._options = {
            -1: "noise_control_disabled",
            3: "noise_control_off_on",
            5: "noise_control_off_on_aw",
            6: "noise_control_on_aw",
            9: "noise_control_off_an"
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\x17", [1, 2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(1)
        if len(value) == 1:
            value = int.from_bytes(value, byteorder="big", signed=True)
            await self.driver.put_property("action", "long_tap",
                                           self._options.get(value, value))
            await self.driver.put_property("action", "long_tap_options",
                                           ",".join(self._options.values()))

    async def set_property(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage.change_rq(b"\x2b\x16", [
            (1, reverse_dict(self._options)[value]),
            (2, reverse_dict(self._options)[value]),
        ])
        resp = await self.driver.send_package(pkg)
        if resp.find_param(2)[0] == 0:
            await self.driver.put_property(group, prop, value)
