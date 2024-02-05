from openfreebuds.device.huawei.generic.spp_device import GenericHuaweiSppDevice
from openfreebuds.device.huawei.spp_handlers.anc_control import AncSettingHandler
from openfreebuds.device.huawei.spp_handlers.battery import BatteryHandler
from openfreebuds.device.huawei.spp_handlers.config_equalizer import BuiltInEqualizerHandler
from openfreebuds.device.huawei.spp_handlers.config_sound_quality import ConfigSoundQualityHandler
from openfreebuds.device.huawei.spp_handlers.device_info import DeviceInfoHandler
from openfreebuds.device.huawei.spp_handlers.dual_connect_devices import DualConnectDevicesHandler
from openfreebuds.device.huawei.spp_handlers.dual_connect_toggle import DualConnectToggleHandler
from openfreebuds.device.huawei.spp_handlers.gesture_double import DoubleTapConfigHandler
from openfreebuds.device.huawei.spp_handlers.gesture_long_separate import SplitLongTapActionConfigHandler
from openfreebuds.device.huawei.spp_handlers.gesture_swipe import SwipeActionHandler
from openfreebuds.device.huawei.spp_handlers.tws_auto_pause import TwsAutoPauseHandler
from openfreebuds.device.huawei.spp_handlers.tws_in_ear import TwsInEarHandler
from openfreebuds.device.huawei.spp_handlers.voice_language import VoiceLanguageHandler


class FreeBudsPro3Device(GenericHuaweiSppDevice):
    """
    HUAWEI FreeBuds Pro 3
    """
    def __init__(self, address):
        super().__init__(address)
        self.spp_fallback_port = 1
        self.handlers = [
            # May work
            DeviceInfoHandler(),
            AncSettingHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            BatteryHandler(),
            ConfigSoundQualityHandler(),
            BuiltInEqualizerHandler(w_presets={
                5: "default",
                1: "hardbass",
                2: "treble",
                9: "voice",
            }),
            TwsAutoPauseHandler(),
            DualConnectToggleHandler(),
            # Not tested, no research data
            DualConnectDevicesHandler(),
            TwsInEarHandler(),
            VoiceLanguageHandler(),
            DoubleTapConfigHandler(),
            SplitLongTapActionConfigHandler(w_right=True),
            SwipeActionHandler(),
        ]
