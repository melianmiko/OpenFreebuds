import logging

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage

log = logging.getLogger("HuaweiHandlers")


class SplitLongTapActionConfigHandler(HuaweiSppHandler):
    """
    Long tap ANC mode cycle setting.

    For devices who store this option in two separate parameters:
    long tap action and preferred modes

    Tested on 4i
    """

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


class DoubleTapConfigHandler(HuaweiSppHandler):
    """
    Double tap config handler
    """
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


class LongTapAction(HuaweiSppHandler):
    """
    Long tap config handler

    For devices without separate left/right long tap setup,
    and without split prop conf.
    """
    handle_commands = [b"\x2b\x17"]
    ignore_commands = [b"\x2b\x16"]

    handle_props = [
        ("action", "long_tap"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x17", [
            (1, b""),
            (2, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(1)
        if len(value) == 1:
            value = int.from_bytes(value, byteorder="big", signed=True)
            self.device.put_property("action", "long_tap", value)

    def on_prop_changed(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage(b"\x2b\x16", [
            (1, value),
            (2, value),
        ])
        self.device.send_package(pkg)

        # Re-read
        self.on_init()


class PowerButtonConfigHandler(HuaweiSppHandler):
    """
    Power button double tap config handler
    """
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


class TouchpadConfigHandler(HuaweiSppHandler):
    """
    Didn't work, for now. Need more research
    """
    handle_commands = [b'\x01-']

    handle_props = [
        ("config", "touchpad_enabled"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2d\x01", [
            (1, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        data = package.find_param(1)
        if len(data) == 1:
            self.device.put_property("config", "touchpad_enabled", data[0])

    def on_prop_changed(self, group: str, prop: str, value):
        self.device.send_package(HuaweiSppPackage(b"\x01\x2c", [
            (1, value),
        ]))
