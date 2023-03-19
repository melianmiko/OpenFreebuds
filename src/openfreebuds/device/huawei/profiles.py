from openfreebuds.device.huawei.generic.spp_device import GenericHuaweiSppDevice

from openfreebuds.device.huawei.spp_handlers.anc_handlers import *
from openfreebuds.device.huawei.spp_handlers.base_handlers import *
from openfreebuds.device.huawei.spp_handlers.gesture_config_handlers import *
from openfreebuds.device.huawei.spp_handlers.tws_handlers import *


class FreeLaceProDevice(GenericHuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)
        self.ui_data = {
            "anc_levels": {
                "comfort": 1,
                "normal": 0,
                "ultra": 2,
            },
            "action_power_button": {
                -1: "tap_action_off",
                12: "tap_action_switch_device"
            },
            "action_long_tap": {
                -1: "tap_action_off",
                3: "noise_control_1",
                5: "noise_control_2",
                6: "noise_control_3",
                9: "noise_control_4"
            }
        }

        self.handlers = [
            # Drop2b03Handler(),
            DeviceInfoHandler(),
            BatteryHandler(),
            ProAncHandler(),
            AncChangeDetectionHandler(),
            PowerButtonConfigHandler(),
            LongTapAction(),
        ]


class FreeBuds4iDevice(GenericHuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            DropLogsHandler(),
            DeviceInfoHandler(),
            TwsInEarHandler(),
            SimpleAncHandler(),
            BatteryHandler(),
            # TouchpadConfigHandler(),
            DoubleTapConfigHandler(),
            SplitLongTapActionConfigHandler(),
            TwsAutoPauseHandler(),
            VoiceLanguageHandler(),
        ]
