import struct

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict

KNOWN_OPTIONS = {
    -1: "tap_action_off",
    1: "tap_action_pause",
    2: "tap_action_next",
    7: "tap_action_prev",
    0: "tap_action_assistant"
}

KNOWN_IN_CALL_OPTIONS = {
    -1: "tap_action_off",
    1: "tap_action_answer",
}


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
        ("action", "double_tap_in_call"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x01\x20", [
            (1, b""),
            (2, b""),
            (3, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        left = package.find_param(1)
        right = package.find_param(2)
        in_call = package.find_param(4)
        available_options = package.find_param(3)
        if len(left) == 1:
            value = int.from_bytes(left, byteorder="big", signed=True)
            self.device.put_property("action", "double_tap_left",
                                     KNOWN_OPTIONS.get(value, value))
        if len(right) == 1:
            value = int.from_bytes(right, byteorder="big", signed=True)
            self.device.put_property("action", "double_tap_right",
                                     KNOWN_OPTIONS.get(value, value))
        if len(available_options) > 0:
            value = list(struct.unpack(f'{len(available_options)}b', available_options))
            out = []
            for v in value:
                out.append(str(v) if v not in KNOWN_OPTIONS else KNOWN_OPTIONS[v])
            self.device.put_property("action", "double_tap_options", ",".join(out))
        if len(in_call) == 1:
            value = int.from_bytes(right, byteorder="big", signed=True)
            self.device.put_property("action", "double_tap_in_call",
                                     KNOWN_IN_CALL_OPTIONS.get(value, value))
            self.device.put_property("action", "double_tap_in_call_options",
                                     ",".join(KNOWN_IN_CALL_OPTIONS.keys()))

    def on_prop_changed(self, group: str, prop: str, value):
        if prop == "double_tap_left":
            p_type = 1
            p_options = KNOWN_OPTIONS
        elif prop == "double_tap_right":
            p_type = 2
            p_options = KNOWN_OPTIONS
        elif prop == "double_tap_in_call":
            p_type = 4
            p_options = KNOWN_IN_CALL_OPTIONS
        else:
            return

        pkg = HuaweiSppPackage(b"\x01\x1f", [
            (p_type, reverse_dict(p_options)[value]),
        ])
        self.device.send_package(pkg)

        # Re-read
        self.on_init()
