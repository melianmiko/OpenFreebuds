import logging

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage

log = logging.getLogger("HuaweiHandlers")


class DropLogsHandler(HuaweiSppHandler):
    ignore_commands = [b"\x0a\x0d"]


# class Drop2b03Handler(HuaweiSppHandler):
#     ignore_commands = [b"\x2b\x03"]


class BatteryHandler(HuaweiSppHandler):
    """
    Battery read handler
    """

    handle_commands = [b'\x01\x08', b'\x01\'']

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x01\x08", [
            (1, b""),
            (2, b""),
            (3, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        out = {}
        if 1 in package.parameters and len(package.parameters[1]) == 1:
            out["global"] = int(package.parameters[1][0])
        if 2 in package.parameters and len(package.parameters[2]) == 3:
            level = package.parameters[2]
            out["left"] = int(level[0])
            out["right"] = int(level[1])
            out["case"] = int(level[2])
        if 3 in package.parameters and len(package.parameters[3]) > 0:
            out["is_charging"] = b"\x01" in package.parameters[3]
        self.device.put_group("battery", out)


class DeviceInfoHandler(HuaweiSppHandler):
    """
    Device info handler
    """

    handle_commands = [b'\x01\x07']

    descriptor = {
        3: "device_ver",
        7: "software_ver",
        9: "serial_number",
        10: "device_model",
        15: "ota_version"
    }

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x01\x07", [
            (1, b""), (2, b""), (3, b""), (4, b""), (5, b""),
            (6, b""), (7, b""), (8, b""), (9, b""), (10, b""),
            (11, b""), (12, b""), (15, b""), (25, b""),
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        out = {}
        for key in package.parameters:
            if key not in self.descriptor:
                log.info(f"Unknown device info field, id={key}, value={package.parameters[key].hex()}")
                continue
            out[self.descriptor[key]] = package.parameters[key].decode("utf8")
        self.device.put_group("info", out)


class VoiceLanguageHandler(HuaweiSppHandler):
    """
    Device voice language read/write handler.
    """

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
                self.device.put_property("service", "supported_languages", locales)

    def on_prop_changed(self, group: str, prop: str, value):
        if group == "service" and prop == "language":
            log.info(f"Set voice language to {value}")
            lang_bytes = value.encode("utf8")
            self.device.send_package(HuaweiSppPackage(b"\x0c\x01", [
                (1, lang_bytes),
                (2, 1)
            ]))
