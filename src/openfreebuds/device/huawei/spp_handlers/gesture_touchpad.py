import logging

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage

log = logging.getLogger("HuaweiHandlers")


class TouchpadConfigHandler(HuaweiSppHandler):
    """
    Didn't work, for now. Need more research
    """

    handler_id = "gesture_touchpad"
    handle_commands = [b'\x01-']

    handle_props = [
        ("config", "touchpad_enabled"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2d\x01", [
            (1, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        data = package.find_param(1)
        if len(data) == 1:
            self.device.put_property("config", "touchpad_enabled", data[0])

    def on_prop_changed(self, group: str, prop: str, value):
        self.device.send_package(HuaweiSppPackage(b"\x01\x2c", [
            (1, value),
        ]))
