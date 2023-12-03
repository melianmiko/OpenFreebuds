from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.tools import reverse_dict

MODE_OPTIONS = {
    0: "normal",
    1: "cancellation",
    2: "awareness",
}

LEVEL_OPTIONS = {
    1: "comfort",
    0: "normal",
    2: "ultra",
}


class ProAncHandler(HuaweiSppHandler):
    """
    Pro ANC mode switching handler.

    For devices with noise-cancellation level configuration.
    """

    handler_id = "anc_pro"
    handle_props = [
        ('anc', 'mode'),
        ('anc', 'level'),
    ]
    handle_commands = [b"\x2b\x2a"]
    ignore_commands = [b"\x2b\x04"]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x2a", [
            (1, b""),
        ]), True)

    def on_package(self, pkg: HuaweiSppPackage):
        data = pkg.find_param(1)
        if len(data) == 2:
            self.device.put_property("anc", "mode", MODE_OPTIONS.get(data[1], data[1]))
            self.device.put_property("anc", "mode_options", ",".join(MODE_OPTIONS.values()))
            self.device.put_property("anc", "level", LEVEL_OPTIONS.get(data[0], data[0]))
            self.device.put_property("anc", "level_options", ",".join(LEVEL_OPTIONS.values()))

    def on_prop_changed(self, group: str, prop: str, value):
        if prop == "mode":
            value = reverse_dict(MODE_OPTIONS)[value]
            value = int(value).to_bytes(1, byteorder="big")
            level = b"\x00" if value == 0 else b"\xff"
            data = value + level
        else:
            # Just change level
            value = reverse_dict(LEVEL_OPTIONS)[value]
            value = int(value).to_bytes(1, byteorder="big")
            data = b"\x01" + value

        self.device.send_package(HuaweiSppPackage(b"\x2b\x04", [
            (1, data),
        ]))
