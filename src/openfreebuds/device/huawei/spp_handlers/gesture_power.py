from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class PowerButtonConfigHandler(HuaweiSppHandler):
    """
    Power button double tap config handler
    """

    handler_id = "gesture_power"
    handle_commands = [b"\x01\x20"]
    ignore_commands = [b"\x01\x1f"]

    handle_props = [
        ("action", "power_button"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x01\x20", [
            (1, b""),
            (2, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        action = package.find_param(1)
        if len(action) == 1:
            value = int.from_bytes(action, byteorder="big", signed=True)
            self.device.put_property("action", "power_button", value)

    def on_prop_changed(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage(b"\x01\x1f", [
            (1, value),
            (2, value),
        ])
        self.device.send_package(pkg)

        # Re-read
        self.on_init()


