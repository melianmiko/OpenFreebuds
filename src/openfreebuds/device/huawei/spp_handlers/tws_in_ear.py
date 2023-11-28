from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class TwsInEarHandler(HuaweiSppHandler):
    """
    TWS in-ear state detection handler
    """

    handler_id = "tws_in_ear"
    handle_commands = [b'+\x03']

    def on_init(self):
        self.device.put_property("state", "in_ear", False)

    def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(8, 9)
        if len(value) == 1:
            self.device.put_property("state", "in_ear", value[0] == 1)
