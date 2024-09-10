from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiLacePro2(OfbDriverHuaweiGeneric):
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiBatteryHandler(w_tws=False),
            OfbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            OfbHuaweiActionLongTapSplitHandler(),
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiEqualizerPresetHandler(w_custom=True),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),
        ]
