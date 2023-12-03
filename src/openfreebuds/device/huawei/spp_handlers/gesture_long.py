from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict

KNOWN_OPTIONS = {
    -1: "noise_control_disabled",
    3: "noise_control_off_on",
    5: "noise_control_off_on_aw",
    6: "noise_control_on_aw",
    9: "noise_control_off_an"
}


class LongTapAction(HuaweiSppHandler):
    """
    Long tap config handler

    For devices without separate left/right long tap setup,
    and without split prop conf.
    """

    handler_id = "gesture_long"
    handle_commands = [b"\x2b\x17"]
    ignore_commands = [b"\x2b\x16"]

    handle_props = [
        ("action", "long_tap"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x17", [
            (1, b""),
            (2, b""),
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(1)
        if len(value) == 1:
            value = int.from_bytes(value, byteorder="big", signed=True)
            self.device.put_property("action", "long_tap",
                                     KNOWN_OPTIONS.get(value, value))
        self.device.put_property("action", "long_tap_options", ",".join(KNOWN_OPTIONS.values()))

    def on_prop_changed(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage(b"\x2b\x16", [
            (1, reverse_dict(KNOWN_OPTIONS)[value]),
            (2, reverse_dict(KNOWN_OPTIONS)[value]),
        ])
        self.device.send_package(pkg)

        # Re-read
        self.on_init()
