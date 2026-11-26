from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiPro3(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds Pro 3
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            # May work
            OfbHuaweiInfoHandler(),
            OfbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            OfbHuaweiBatteryHandler(),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiEqualizerPresetHandler(w_presets={
                5: "default",
                1: "hardbass",
                2: "treble",
                9: "voice",
            }, w_custom=True),
            OfbHuaweiConfigAutoPauseHandler(),
            # Not tested, no research data
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiActionLightHoldHandler(w_light_hold=True, w_pinch_hold=False),
            OfbHuaweiActionLongTapSplitHandler(w_right=True),
            OfbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),
            OfbHuaweiBoxToneHandler(w_lid_tone=False),
        ]
