from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiArc(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeArc
    """
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiActionDoubleTapHandler(w_in_call=True),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiActionLongTapSplitHandler(w_right=True, w_in_call=True, w_anc=False),
            OfbHuaweiActionSwipeGestureSplitHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),
            OfbHuaweiEqualizerPresetHandler(w_presets={
                1: "default",
                10: "dynamic",
                2: "hardbass",
                3: "treble",
                9: "voices",
            }, w_custom=True),
            OfbHuaweiDualConnectHandler(),
        ]
