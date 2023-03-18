import logging

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage

log = logging.getLogger("HuaweiHandlers")


class TwsAutoPauseHandler(HuaweiSppHandler):
    """
    TWS pause when plug off config handler
    """

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
            self.device.put_property("config", "auto_pause", data[0])

    def on_prop_changed(self, group: str, prop: str, value):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x10", [
            (1, value)
        ]), True)


class TwsInEarHandler(HuaweiSppHandler):
    """
    TWS in-ear state detection handler
    """

    handle_commands = [b'+\x03']

    def on_init(self):
        self.device.put_property("state", "in_ear", False)

    def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(8, 9)
        if len(value) == 1:
            self.device.put_property("state", "in_ear", value[0] == 1)
