from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiStudio(OfbDriverHuaweiGeneric):
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiBatteryHandler(w_tws=False),
            OfbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            OfbHuaweiConfigAutoPauseHandler(),
            OfbHuaweiEqualizerPresetHandler(wo_read=True, w_presets={
                1: "default",
                2: "hardbass",
                3: "treble",
            }),
        ]
