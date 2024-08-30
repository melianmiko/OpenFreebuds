from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class FbDriverHuawei5i(FbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds 5i
    """
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            FbHuaweiInfoHandler(),
            FbHuaweiStateInEarHandler(),
            FbHuaweiBatteryHandler(),
            FbHuaweiAncHandler(w_cancel_lvl=True),
            FbHuaweiActionDoubleTapHandler(w_in_call=True),
            FbHuaweiActionLongTapSplitHandler(w_right=True),
            FbHuaweiActionSwipeGestureHandler(),
            FbHuaweiConfigAutoPauseHandler(),
            FnHuaweiSoundQualityPreferenceHandler(),
            FbHuaweiEqualizerPresetHandler(w_presets={
                1: "default",
                2: "hardbass",
                3: "treble",
                9: "voices",
            }),
            FbHuaweiVoiceLanguageHandler(),
            FbHuaweiDualConnectToggleHandler(),
            FbHuaweiDualConnectHandler(),
        ]
