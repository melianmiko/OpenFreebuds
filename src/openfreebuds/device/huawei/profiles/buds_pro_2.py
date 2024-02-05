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


class FreeBudsPro2Device(GenericHuaweiSppDevice):
    """
    HUAWEI FreeBuds Pro 2
    """
    def __init__(self, address):
        super().__init__(address)
        self.spp_fallback_port = 1
        self.handlers = [
            DeviceInfoHandler(),
            TwsInEarHandler(),
            BatteryHandler(),
            AncSettingHandler(w_cancel_lvl=True),
            SplitLongTapActionConfigHandler(w_right=True),
            SwipeActionHandler(),
            TwsAutoPauseHandler(),
            ConfigSoundQualityHandler(),
            BuiltInEqualizerHandler(w_presets={
                1: "default",
                2: "hardbass",
                3: "treble",
            }),
            DualConnectToggleHandler(),
            DualConnectDevicesHandler(),
            VoiceLanguageHandler(),
        ]
