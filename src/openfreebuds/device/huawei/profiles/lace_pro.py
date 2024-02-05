from openfreebuds.device.huawei.generic.spp_device import GenericHuaweiSppDevice
from openfreebuds.device.huawei.spp_handlers.anc_change import AncChangeDetectionHandler
from openfreebuds.device.huawei.spp_handlers.anc_control import AncSettingHandler
from openfreebuds.device.huawei.spp_handlers.battery import BatteryHandler
from openfreebuds.device.huawei.spp_handlers.device_info import DeviceInfoHandler
from openfreebuds.device.huawei.spp_handlers.gesture_long import LongTapAction
from openfreebuds.device.huawei.spp_handlers.gesture_power import PowerButtonConfigHandler


class FreeLaceProDevice(GenericHuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)

        # Add cooldown to prevent device hang
        self.spp_connect_sleep = 2

        self.handlers = [
            # Drop2b03Handler(),
            DeviceInfoHandler(),
            BatteryHandler(),
            AncSettingHandler(w_cancel_lvl=True, w_reply_nowait=True),
            AncChangeDetectionHandler(),
            PowerButtonConfigHandler(),
            LongTapAction(),
        ]
