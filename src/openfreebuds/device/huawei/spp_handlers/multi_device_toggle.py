from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class MultiDeviceToggleHandler(HuaweiSppHandler):
    """
    Enable/disable multi-device support (pro 3, maybe 5i)
    """
    handler_id = "multi_device_toggle"
    handle_commands = (
        b"\x2b\x2f"
    )
    ignore_commands = (
        b"\x2b\x2e",
    )
    handle_props = (
        ("multi_device", "enabled"),
    )

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x2f", [
            (1, b""),
        ]))

    def on_prop_changed(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage(b"\x2b\x2e", [
            (1, 1 if value else 0),
        ])
        self.device.send_package(pkg)
        self.on_init()

    def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(1)

        if len(value) == 1:
            value = int(value[0])
            self.device.put_property("multi_device", "enabled", value)
