from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict

KNOWN_OPTIONS = {
    0: "sqp_quality",
    1: "sqp_connectivity",
}


class ConfigSoundQualityHandler(HuaweiSppHandler):
    """
    Sound quality preference option from 5i, and maybe other devices too
    """
    handler_id = "config_sound_quality"
    handle_commands = [
        b"\x2b\xa3",
    ]
    ignore_commands = [
        b"\x2b\xa2",
    ]
    handle_props = [
        ("config", "sound_quality_preference"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\xa3", [
            (1, b""),
        ]))

    def on_prop_changed(self, group: str, prop: str, value):
        value = reverse_dict(KNOWN_OPTIONS)[value]
        pkg = HuaweiSppPackage(b"\x2b\xa2", [
            (1, value),
        ])

        self.device.send_package(pkg)

        # self.on_init()

    def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(2)

        if len(value) == 1:
            value = int.from_bytes(value, byteorder="big", signed=True)
            self.device.put_property("config", "sound_quality_preference",
                                     KNOWN_OPTIONS[value])
            self.device.put_property("config", "sound_quality_preference_options",
                                     ",".join(KNOWN_OPTIONS.values()))
