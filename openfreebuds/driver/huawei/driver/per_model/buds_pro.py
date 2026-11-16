from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiPro(OfbDriverHuaweiGeneric):
    # FreeBuds Pro (1st gen) is one of two models without find-earbud support in the official capability matrix
    supports_find_earbud = False

    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            OfbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiActionLongTapSplitHandler(w_right=True),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiDualConnectHandler(),
        ]
