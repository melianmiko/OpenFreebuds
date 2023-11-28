from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class SplitLongTapActionConfigHandler(HuaweiSppHandler):
    """
    Long tap ANC mode cycle setting.

    For devices who store this option in two separate parameters:
    long tap action and preferred modes

    Tested on 4i
    """

    handler_id = "gesture_long_split"
    handle_commands = [
        b'+\x17',
        b'+\x19'
    ]
    ignore_commands = [
        b'+\x16',
        b'+\x18'
    ]
    handle_props = [
        ("action", "long_tap_left"),
        ("action", "long_tap_right"),
        ("action", "noise_control_left"),
        ("action", "noise_control_right"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x17", [
            (1, b""),
            (2, b"")
        ]), True)
        self.device.send_package(HuaweiSppPackage(b"\x2b\x19", [
            (1, b""),
            (2, b"")
        ]), True)

    def on_prop_changed(self, group: str, prop: str, value):
        p_type = 1 if prop.endswith("left") else 2

        if prop.startswith("long_tap"):
            # Main action
            pkg = HuaweiSppPackage(b"\x2b\x16", [
                (p_type, value),
            ])
        else:
            # ANC modes
            pkg = HuaweiSppPackage(b"\x2b\x18", [
                (p_type, value),
            ])

        self.device.send_package(pkg)

        # Request re-read of changed props
        self.on_init()

    def on_package(self, package: HuaweiSppPackage):
        left = package.find_param(1)
        right = package.find_param(2)
        if package.command_id == b"+\x17":
            if len(left) == 1:
                value = int.from_bytes(left, byteorder="big", signed=True)
                self.device.put_property("action", "long_tap_left", value)
            if len(right) == 1:
                value = int.from_bytes(right, byteorder="big", signed=True)
                self.device.put_property("action", "long_tap_right", value)
        elif package.command_id == b'+\x19':
            if len(left) == 1:
                value = int.from_bytes(left, byteorder="big", signed=True)
                self.device.put_property("action", "noise_control_left", value)
            if len(right) == 1:
                value = int.from_bytes(right, byteorder="big", signed=True)
                self.device.put_property("action", "noise_control_right", value)
