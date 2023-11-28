from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class BatteryHandler(HuaweiSppHandler):
    """
    Battery read handler
    """

    handler_id = "battery"
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


