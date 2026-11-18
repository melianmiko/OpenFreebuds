from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuawei7I(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds 7i

    In-ear ANC earbuds with on-device spatial audio and head motion
    controls. No adaptive volume, no charging box tone customisation.

    Handler set is derived from the official feature matrix and
    config_ZAAU.json, not device-tested (no hardware available).
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True, w_voice_boost=True),
            OfbHuaweiBatteryHandler(),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiEqualizerPresetHandler(w_presets={
                1: "default",
                2: "hardbass",
                3: "treble",
                9: "voices",
            }, w_custom=True),
            OfbHuaweiConfigAutoPauseHandler(),
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiVoiceLanguageHandler(),

            # Gestures
            OfbHuaweiActionDoubleTapHandler(w_in_call=True),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiActionLongTapSplitHandler(w_right=True, w_in_call=True),
            OfbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),

            # Device features
            OfbHuaweiSpatialAudioHandler(),
            OfbHuaweiHeadControlHandler(),
        ]
