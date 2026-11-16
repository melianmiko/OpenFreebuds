from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiNeo(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds Neo

    In-ear ANC earbuds with on-device spatial audio, adaptive volume
    and head motion controls. No charging box tone customisation.

    Handler set is derived from the official feature matrix and
    config_ZAB4.json, not device-tested (no hardware available).
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
                5: "default",
                2: "hardbass",
                3: "treble",
                9: "voices",
            }),
            OfbHuaweiConfigAutoPauseHandler(),
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiVoiceLanguageHandler(),

            # Gestures
            OfbHuaweiActionDoubleTapHandler(),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiActionLongTapSplitHandler(w_right=True),
            OfbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),

            # Device features
            OfbHuaweiSpatialAudioHandler(),
            OfbHuaweiAdaptiveVolumeHandler(),
            OfbHuaweiHeadControlHandler(),
            OfbHuaweiDropReminderHandler(),
        ]
