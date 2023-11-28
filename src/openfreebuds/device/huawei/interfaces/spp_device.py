from openfreebuds.device.generic.spp_device import GenericSppDevice
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class HuaweiSppDevice(GenericSppDevice):
    def send_package(self, pkg: HuaweiSppPackage, read=False):
        raise NotImplementedError("send_package")
