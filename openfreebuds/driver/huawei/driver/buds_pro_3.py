from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class FbDriverHuaweiPro3(FbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds Pro 3
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            # May work
            FbHuaweiInfoHandler(),
            FbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            FbHuaweiBatteryHandler(),
            FnHuaweiSoundQualityPreferenceHandler(),
            FbHuaweiEqualizerPresetHandler(w_presets={
                5: "default",
                1: "hardbass",
                2: "treble",
                9: "voice",
            }),
            FbHuaweiConfigAutoPauseHandler(),
            FbHuaweiDualConnectToggleHandler(),
            # Not tested, no research data
            FbHuaweiDualConnectHandler(),
            FbHuaweiStateInEarHandler(),
            FbHuaweiVoiceLanguageHandler(),
            FbHuaweiActionDoubleTapHandler(),
            FbHuaweiActionLongTapSplitHandler(w_right=True),
            FbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),
        ]
