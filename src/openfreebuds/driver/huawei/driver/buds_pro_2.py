from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class FbDriverHuaweiPro(FbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds Pro 2
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            FbHuaweiInfoHandler(),
            FbHuaweiStateInEarHandler(),
            FbHuaweiBatteryHandler(),
            FbHuaweiAncHandler(w_cancel_lvl=True),
            FbHuaweiActionLongTapSplitHandler(w_right=True),
            FbHuaweiActionSwipeGestureHandler(),
            FbHuaweiConfigAutoPauseHandler(),
            FnHuaweiSoundQualityPreferenceHandler(),
            FbHuaweiEqualizerPresetHandler(w_presets={
                1: "default",
                2: "hardbass",
                3: "treble",
            }),
            FbHuaweiDualConnectToggleHandler(),
            FbHuaweiDualConnectHandler(),
            FbHuaweiVoiceLanguageHandler(),
        ]
