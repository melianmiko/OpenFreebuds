from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuawei6(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds 6

    Half-in-ear earbuds without ANC. Supports on-device sound quality,
    adaptive volume, charging box tone customisation and head motion
    controls. Spatial audio is computed on a HarmonyOS phone, so it is
    not exposed here.

    Handler set is derived from the official feature matrix and
    config_ZAAL.json, not device-tested (no hardware available).
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiBatteryHandler(),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiEqualizerPresetHandler(w_presets={
                0: "default",
                2: "hardbass",
                3: "treble",
                9: "voices",
            }),
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
            OfbHuaweiAdaptiveVolumeHandler(),
            OfbHuaweiBoxToneHandler(),
            OfbHuaweiHeadControlHandler(),
            OfbHuaweiDropReminderHandler(),
        ]
