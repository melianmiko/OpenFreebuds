import time

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict

MODE_OPTIONS = {
    0: "normal",
    1: "cancellation",
    2: "awareness",
}


class AncSettingHandler(HuaweiSppHandler):
    """
    ANC mode switching handler.
    """

    handler_id = "anc_global"
    handle_props = [
        ('anc', 'mode'),
        ('anc', 'level'),
    ]
    handle_commands = [b"\x2b\x2a"]
    ignore_commands = [b"\x2b\x04"]

    def __init__(self, w_cancel_lvl=False, w_reply_nowait=False, w_cancel_dynamic=False, w_voice_boost=False):
        self.w_cancel_lvl = w_cancel_lvl
        self.w_reply_nowait = w_reply_nowait
        self.w_voice_boost = w_voice_boost
        self.active_mode = 0

        self.cancel_level_options = {
            1: "comfort",
            0: "normal",
            2: "ultra",
        }

        self.awareness_level_options = {
            2: "normal",
        }

        if w_cancel_dynamic:
            self.cancel_level_options[3] = "dynamic"
        if w_voice_boost:
            self.awareness_level_options[1] = "voice_boost"

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x2a", [
            (1, b""),
        ]))

    def on_package(self, pkg: HuaweiSppPackage):
        data = pkg.find_param(1)

        if len(data) == 2:
            self.active_mode = data[1]
            new_props = {
                "mode": MODE_OPTIONS.get(data[1], data[1]),
                "mode_options": ",".join(MODE_OPTIONS.values()),
            }

            if data[1] == 1 and self.w_cancel_lvl:
                # If cancellation turned on and support levels, list them
                new_props["level"] = self.cancel_level_options.get(data[0], data[0])
                new_props["level_options"] = ",".join(self.cancel_level_options.values())

            if data[1] == 2 and self.w_voice_boost:
                # If awareness turned on and support voice boost
                new_props["level"] = "voice_boost" if data[0] != 0 else "normal"
                new_props["level_options"] = "normal,voice_boost"

            self.device.put_group("anc", new_props)

    def on_prop_changed(self, group: str, prop: str, value):
        if prop == "mode":
            value_bytes = reverse_dict(MODE_OPTIONS)[value]
            value_bytes = int(value_bytes).to_bytes(1, byteorder="big")
            level = b"\x00" if value_bytes == 0 else b"\xff"
            data = value_bytes + level
            if self.w_reply_nowait:
                self.device.put_property("anc", "mode", value)
        else:
            # Just change level
            options = self.cancel_level_options if self.active_mode != 2 else self.awareness_level_options
            value_bytes = reverse_dict(options)[value]
            value_bytes = int(value_bytes).to_bytes(1, byteorder="big")
            mode_bytes = int(self.active_mode).to_bytes(1, byteorder="big")
            data = mode_bytes + value_bytes
            if self.w_reply_nowait:
                self.device.put_property("anc", "level", value)

        self.device.send_package(HuaweiSppPackage(b"\x2b\x04", [
            (1, data),
        ]), read=not self.w_reply_nowait)

        if self.w_reply_nowait:
            # For buggy devices like FreeLace Pro
            time.sleep(0.5)
        self.on_init()
