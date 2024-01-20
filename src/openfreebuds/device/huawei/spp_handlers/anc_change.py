import time

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class AncChangeDetectionHandler(HuaweiSppHandler):
    """
    This handler wait for 2b03 command package to
    detect ANC mode change via on-device button
    """
    handler_id = "anc_change"
    handle_commands = [b"\x2b\x03"]

    def on_package(self, package: HuaweiSppPackage):
        data = package.find_param(1)
        if len(data) == 1 and 0 <= data[0] <= 2:
            self.device.send_package(HuaweiSppPackage(b"\x2b\x2a", [
                (1, b""),
            ]))
