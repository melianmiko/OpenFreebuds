from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict

KNOWN_OPTIONS = {
    -1: "tap_action_off",
    0: "tap_action_change_volume",
}


class SwipeActionHandler(HuaweiSppHandler):
    """
    Swipe action setting handler.
    Supported on 5i, maybe also on Pro-devices
    """
    handler_id = "gesture_swipe"
    handle_commands = (
        b"\x2b\x1f"
    )
    ignore_commands = (
        b"\x2b\1e"
    )
    handle_props = (
        ("action", "swipe_gesture"),
    )

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x1f", [
            (1, b""),
            (2, b""),
        ]))

    def on_prop_changed(self, group: str, prop: str, value):
        value = reverse_dict(KNOWN_OPTIONS)[value]
        pkg = HuaweiSppPackage(b"\x2b\x1e", [
            (1, value),
            (2, value)
        ])

        self.device.send_package(pkg)

        # re-read
        self.on_init()

    def on_package(self, package: HuaweiSppPackage):
        left = package.find_param(1)
        if len(left) == 1:
            value = int.from_bytes(left, byteorder="big", signed=True)
            self.device.put_property("action", "swipe_gesture",
                                     KNOWN_OPTIONS.get(value, value))
            self.device.put_property("action", "swipe_gesture_options",
                                     ",".join(KNOWN_OPTIONS.keys()))
