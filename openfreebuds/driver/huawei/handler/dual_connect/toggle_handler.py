from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiDualConnectToggleHandler(OfbDriverHandlerHuawei):
    """
    Enable/disable multi-device support (pro 3, 5i)
    """
    handler_id = "dual_connect_toggle"
    commands = [b"\x2b\x2f"]
    ignore_commands = [b"\x2b\x2e"]
    properties = [
        ("config", "dual_connect"),
    ]

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\x2f", [1]))
        await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage.change_rq(b"\x2b\x2e", [
            (1, 1 if value == "true" else 0),
        ])
        await self.driver.send_package(pkg)
        await self.init()

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(1)

        if len(value) == 1:
            value = int(value[0])
            await self.driver.put_property("config", "dual_connect", "true" if value == 1 else "false")
