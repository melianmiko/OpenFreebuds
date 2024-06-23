from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class FbDriverHuaweiPro(FbDriverHuaweiGeneric):
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            FbHuaweiInfoHandler(),
            FbHuaweiStateInEarHandler(),
            FbHuaweiBatteryHandler(),
            FbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            FbHuaweiActionSwipeGestureHandler(),
            FbHuaweiStateInEarHandler(),
            FbHuaweiActionLongTapSplitHandler(w_right=True),
            FbHuaweiVoiceLanguageHandler(),
            FbHuaweiDualConnectHandler(),
            FbHuaweiDualConnectToggleHandler(),
        ]
