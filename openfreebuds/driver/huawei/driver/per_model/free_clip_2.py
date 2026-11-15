from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiFreeClip2(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeClip 2

    Open-ear clip-on earbuds (2nd gen). No traditional ANC,
    supports double/triple tap, swipe gestures, custom EQ,
    dual-connect, head motion controls, and more.
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            # Confirmed working features
            OfbHuaweiInfoHandler(),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiConfigAutoPauseHandler(),

            # Gesture handlers
            OfbHuaweiActionDoubleTapHandler(),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiActionLongTapSplitHandler(w_agent_modes=True, w_anc=False),
            OfbHuaweiActionSwipeGestureHandler(),

            # Sound & audio quality
            OfbHuaweiEqualizerPresetHandler(w_presets={
                1: "default",
                2: "hardbass",
                3: "treble",
                9: "voices",
            }, w_custom=True, w_custom_rows=10, w_custom_max_count=3),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),

            # Device features
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiSpatialAudioHandler(),
            OfbHuaweiAdaptiveVolumeHandler(),
            OfbHuaweiBoxToneHandler(),
            OfbHuaweiHeadControlHandler(),

            # Not tested / unsupported on FreeClip 2:
            # - ANC (open-ear, no traditional ANC)
            # - Drop reminder - needs SPP research
        ]
