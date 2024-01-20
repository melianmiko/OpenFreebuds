from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict

KNOWN_OPTIONS = {
    1: "equalizer_preset_default",
    2: "equalizer_preset_hardbass",
    3: "equalizer_preset_treble",
}


class EqualizerConfigHandler(HuaweiSppHandler):
    """
    Built-in equalizer settings handler (5i)
    """
    handler_id = "config_eq"
    handle_commands = (
        b"\x2b\x4a",
    )
    ignore_commands = (
        b"\x2b\x49",
    )
    handle_props = (
        ("config", "equalizer_preset")
    )

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x49", [
            (2, b""),
        ]))

    def on_prop_changed(self, group: str, prop: str, value):
        value = reverse_dict(KNOWN_OPTIONS)[value]
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
                                     KNOWN_OPTIONS[value])
            self.device.put_property("config", "equalizer_preset_options",
                                     ",".join(KNOWN_OPTIONS.keys()))
