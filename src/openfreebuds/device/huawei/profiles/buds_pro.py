from openfreebuds.device.huawei.generic.spp_device import GenericHuaweiSppDevice
from openfreebuds.device.huawei.spp_handlers.anc_control import AncSettingHandler
from openfreebuds.device.huawei.spp_handlers.battery import BatteryHandler
from openfreebuds.device.huawei.spp_handlers.device_info import DeviceInfoHandler
from openfreebuds.device.huawei.spp_handlers.gesture_double import DoubleTapConfigHandler
from openfreebuds.device.huawei.spp_handlers.gesture_long_separate import SplitLongTapActionConfigHandler
from openfreebuds.device.huawei.spp_handlers.gesture_swipe import SwipeActionHandler
from openfreebuds.device.huawei.spp_handlers.tws_in_ear import TwsInEarHandler
from openfreebuds.device.huawei.spp_handlers.voice_language import VoiceLanguageHandler


class FreeBudsProDevice(GenericHuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)
        self.spp_fallback_port = 1
        self.handlers = [
            DeviceInfoHandler(),
            TwsInEarHandler(),
            BatteryHandler(),
            AncSettingHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            # not tested, no information
            SwipeActionHandler(),
            TwsInEarHandler(),
            DoubleTapConfigHandler(),
            SplitLongTapActionConfigHandler(w_right=True),
            VoiceLanguageHandler(),
        ]
