from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict

KNOWN_LONG_TAP_OPTIONS = {
    -1: "tap_action_off",
    10: "tap_action_switch_anc"
}

KNOWN_ANC_OPTIONS = {
    1: "noise_control_off_on",
    2: "noise_control_off_on_aw",
    3: "noise_control_on_aw",
    4: "noise_control_off_an"
}

KNOWN_LONG_TAP_IN_CALL_OPTIONS = {
    -1: "tap_action_off",
    0: "tap_action_answer"
}


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
        ("action", "noise_control_in_call"),
    ]

    def __init__(self, w_right=False, w_in_call=False):
        self.w_right = w_right
        self.w_in_call = w_in_call

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
        if "_left" in prop:
            p_type = 1
            p_options = KNOWN_LONG_TAP_OPTIONS
        elif "_right" in prop:
            p_type = 2
            p_options = KNOWN_LONG_TAP_OPTIONS
        elif "_in_call" in prop:
            p_type = 4
            p_options = KNOWN_LONG_TAP_IN_CALL_OPTIONS
        else:
            return

        if prop.startswith("long_tap"):
            # Main action
            pkg = HuaweiSppPackage(b"\x2b\x16", [
                (p_type, reverse_dict(p_options)[value]),
            ])
        else:
            # ANC modes
            pkg = HuaweiSppPackage(b"\x2b\x18", [
                (p_type, reverse_dict(KNOWN_ANC_OPTIONS)[value]),
            ])

        self.device.send_package(pkg)

        # Request re-read of changed props
        self.on_init()

    def on_package(self, package: HuaweiSppPackage):
        left = package.find_param(1)
        right = package.find_param(2)
        in_call = package.find_param(4)
        if package.command_id == b"+\x17":
            if len(left) == 1:
                value = int.from_bytes(left, byteorder="big", signed=True)
                self.device.put_property("action", "long_tap_left",
                                         KNOWN_LONG_TAP_OPTIONS.get(value, value))
            if len(right) == 1 and self.w_right:
                value = int.from_bytes(right, byteorder="big", signed=True)
                self.device.put_property("action", "long_tap_right",
                                         KNOWN_LONG_TAP_OPTIONS.get(value, value))
            if len(in_call) == 1 and self.w_in_call:
                value = int.from_bytes(right, byteorder="big", signed=True)
                self.device.put_property("action", "long_tap_in_call",
                                         KNOWN_LONG_TAP_IN_CALL_OPTIONS.get(value, value))
                self.device.put_property("action", "long_tap_in_call_options",
                                         ",".join(KNOWN_LONG_TAP_IN_CALL_OPTIONS.keys()))
            self.device.put_property("action", "long_tap_options", ",".join(KNOWN_LONG_TAP_OPTIONS.values()))
        elif package.command_id == b'+\x19':
            if len(left) == 1:
                value = int.from_bytes(left, byteorder="big", signed=True)
                self.device.put_property("action", "noise_control_left",
                                         KNOWN_ANC_OPTIONS.get(value, value))
            if len(right) == 1 and self.w_right:
                value = int.from_bytes(right, byteorder="big", signed=True)
                self.device.put_property("action", "noise_control_right",
                                         KNOWN_ANC_OPTIONS.get(value, value))
            self.device.put_property("action", "noise_control_options", ",".join(KNOWN_ANC_OPTIONS.values()))
            # if len(available_options) > 0:
            #     value = list(struct.unpack(f'{len(available_options)}b', available_options))
            #     out = []
            #     for v in value:
            #         if v in KNOWN_ANC_OPTIONS:
            #             out.append(str(v))
            #     self.device.put_property("action", "noise_control_options", ",".join(out))
