from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class VoiceLanguageHandler(HuaweiSppHandler):
    """
    Device voice language read/write handler.
    """

    handler_id = "voice_language"
    handle_props = [
        ("service", "language")
    ]
    handle_commands = [b'\x0c\x02']
    ignore_commands = [b"\x0c\x01"]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x0c\x02", [
            (1, b""),
            (3, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        if package.command_id == b"\x0c\x02":
            if 3 in package.parameters and len(package.parameters[3]) > 1:
                locales = package.parameters[3].decode("utf8")
                self.device.put_property("service", "language", "")
                self.device.put_property("service", "supported_languages", locales)

    def on_prop_changed(self, group: str, prop: str, value):
        if group == "service" and prop == "language":
            lang_bytes = value.encode("utf8")
            self.device.send_package(HuaweiSppPackage(b"\x0c\x01", [
                (1, lang_bytes),
                (2, 1)
            ]))
