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
    commands = [b'\x0c\x02']
    ignore_commands = [b"\x0c\x01"]

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x0c\x02", [1, 2]))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if 3 in package.parameters and len(package.parameters[3]) > 1:
            locales = package.parameters[3].decode("utf8")
            await self.driver.put_property("service", "language", self._active_locale(package, locales))
            await self.driver.put_property("service", "language_options", locales)

    @staticmethod
    def _active_locale(package: HuaweiSppPackage, locales: str) -> str:
        # Param 4 carries the index of the locale the device is currently using.
        # Devices that don't report it (or report something out of range) keep
        # the old behaviour of leaving the selection blank.
        index = package.parameters.get(4, b"")
        if len(index) != 1:
            return ""

        options = locales.split(",")
        return options[index[0]] if index[0] < len(options) else ""

    async def set_property(self, group: str, prop: str, value):
        lang_bytes = value.encode("utf8")
        await self.driver.send_package(HuaweiSppPackage.change_rq(b"\x0c\x01", [
            (1, lang_bytes),
            (2, 1)
        ]))

        # Some models acknowledge the write but keep their language, so read the
        # state back instead of assuming the new value took effect.
        await self.on_init()
