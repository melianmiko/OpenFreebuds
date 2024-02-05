from openfreebuds.device.huawei.generic.spp_device import GenericHuaweiSppDevice
from openfreebuds.device.huawei.spp_handlers.battery import BatteryHandler
from openfreebuds.device.huawei.spp_handlers.device_info import DeviceInfoHandler
from openfreebuds.device.huawei.spp_handlers.drop import DropLogsHandler
from openfreebuds.device.huawei.spp_handlers.gesture_double import DoubleTapConfigHandler


class FreeBudsSEDevice(GenericHuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            DropLogsHandler(),
            DeviceInfoHandler(),
            BatteryHandler(),
            DoubleTapConfigHandler(),
        ]
