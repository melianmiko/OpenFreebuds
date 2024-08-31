from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiVoiceLanguageHandler(OfbDriverHandlerHuawei):
    """
    Device voice language read/write handler.
    """

    handler_id = "voice_language"
    properties = [
        ("service", "language")
    ]
    handle_commands = [b'\x0c\x02']
    ignore_commands = [b"\x0c\x01"]

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x0c\x02", [1, 2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if 3 in package.parameters and len(package.parameters[3]) > 1:
            locales = package.parameters[3].decode("utf8")
            await self.driver.put_property("service", "language", "")
            await self.driver.put_property("service", "language_options", locales)

    async def set_property(self, group: str, prop: str, value):
        lang_bytes = value.encode("utf8")
        await self.driver.send_package(HuaweiSppPackage.change_rq(b"\x0c\x01", [
            (1, lang_bytes),
            (2, 1)
        ]))
