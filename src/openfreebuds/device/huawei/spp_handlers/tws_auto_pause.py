import logging

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage

log = logging.getLogger("HuaweiHandlers")


class TwsAutoPauseHandler(HuaweiSppHandler):
    """
    TWS pause when plug off config handler
    """

    handler_id = "tws_auto_pause"
    handle_commands = [b'\x2b\x11', b'\x2b\x10']
    handle_props = [
        ("config", "auto_pause"),
    ]

    def on_init(self):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x11", [
            (1, b"")
        ]), True)

    def on_package(self, package: HuaweiSppPackage):
        data = package.find_param(1)
        if len(data) == 1:
            self.device.put_property("config", "auto_pause", data[0] == 1)

    def on_prop_changed(self, group: str, prop: str, value):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x10", [
            (1, 1 if value else 0)
        ]), True)
        self.on_init()
