from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class DeviceInfoHandler(HuaweiSppHandler):
    """
    Device info handler
    """

    handler_id = "device_info"
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
            out[self.descriptor.get(key, f"field_{key}")] = package.parameters[key].decode("utf8")
        self.device.put_group("info", out)
