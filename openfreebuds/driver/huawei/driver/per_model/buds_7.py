from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuawei7(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds 7

    In-ear ANC earbuds with on-device spatial audio, adaptive volume,
    charging box tone and head motion controls.

    Handler set is derived from the official feature matrix and
    config_ZAB1.json, not device-tested (no hardware available).
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True),
            OfbHuaweiBatteryHandler(),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiEqualizerPresetHandler(w_presets={
                5: "default",
                1: "hardbass",
                2: "treble",
                9: "voices",
            }, w_custom=True),
            OfbHuaweiConfigAutoPauseHandler(),
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiVoiceLanguageHandler(),

            # Gestures
            OfbHuaweiActionDoubleTapHandler(w_in_call=True, w_read_in_call=True),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiActionLightHoldHandler(w_light_hold=True, w_pinch_hold=True),
            OfbHuaweiActionLongTapSplitHandler(w_right=True),
            OfbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),

            # Device features
            OfbHuaweiSpatialAudioHandler(),
            OfbHuaweiAdaptiveVolumeHandler(),
            OfbHuaweiBoxToneHandler(),
            OfbHuaweiHeadControlHandler(),
            OfbHuaweiDropReminderHandler(),
        ]
