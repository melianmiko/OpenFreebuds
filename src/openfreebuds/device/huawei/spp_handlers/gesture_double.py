from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class DoubleTapConfigHandler(HuaweiSppHandler):
    """
    Double tap config handler
    """

    handler_id = "gesture_double"
    handle_commands = [b"\x01\x20"]
    ignore_commands = [b"\x01\x1f"]

    handle_props = [
        ("action", "double_tap_left"),
        ("action", "double_tap_right"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x01\x20", [
            (1, b""),
            (2, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        left = package.find_param(1)
        right = package.find_param(2)
        if len(left) == 1:
            value = int.from_bytes(left, byteorder="big", signed=True)
            self.device.put_property("action", "double_tap_left", value)
        if len(right) == 1:
            value = int.from_bytes(right, byteorder="big", signed=True)
            self.device.put_property("action", "double_tap_right", value)

    def on_prop_changed(self, group: str, prop: str, value):
        p_type = 1 if prop.endswith("left") else 2
        pkg = HuaweiSppPackage(b"\x01\x1f", [
            (p_type, value),
        ])
        self.device.send_package(pkg)

        # Re-read
        self.on_init()


