from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict


class BuiltInEqualizerHandler(HuaweiSppHandler):
    """
    Built-in equalizer settings handler (5i)
    """
    handler_id = "config_eq"
    handle_commands = [
        b"\x2b\x4a",
    ]
    ignore_commands = [
        b"\x2b\x49",
    ]
    handle_props = [
        ("config", "equalizer_preset")
    ]

    def __init__(self, w_presets=None):
        self.w_presets = w_presets or {}
        for i in self.w_presets:
            self.w_presets[i] = "equalizer_preset_" + self.w_presets[i]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x4a", [
            (2, b""),
        ]))

    def on_prop_changed(self, group: str, prop: str, value):
        value = reverse_dict(self.w_presets)[value]
        pkg = HuaweiSppPackage(b"\x2b\x49", [
            (1, value),
        ])

        self.device.send_package(pkg)
        self.on_init()

    def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(2)

        if len(value) == 1:
            value = int.from_bytes(value, byteorder="big", signed=True)
            self.device.put_property("config", "equalizer_preset",
                                     self.w_presets[value])
            self.device.put_property("config", "equalizer_preset_options",
                                     ",".join(self.w_presets.values()))
