from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiPro5(OfbDriverHuaweiGeneric):
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
                1: "hardbass",
                2: "treble",
                9: "voice",
            }, w_custom=True),
            OfbHuaweiConfigAutoPauseHandler(),
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiActionLightHoldHandler(w_light_hold=True, w_pinch_hold=True),
            OfbHuaweiActionDoubleTapHandler(
                w_in_call=True, w_read_in_call=True, w_both_ears=True,
                options_map={
                    1: "tap_action_pause",
                    -1: "tap_action_off",
                },
                options_call_map={
                    0: "tap_action_answer_end",
                    -1: "tap_action_off",
                },
            ),
            OfbHuaweiActionTripleTapHandler(options_map={
                2: "tap_action_next",
                7: "tap_action_prev",
                -1: "tap_action_off",
            }),
            OfbHuaweiActionLongTapSplitHandler(
                w_right=True, w_anc=False,
                options_map={
                    0: "tap_action_assistant",
                    10: "tap_action_switch_anc",
                    -1: "tap_action_off",
                },
            ),
            OfbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),
            OfbHuaweiSpatialAudioHandler(),
            OfbHuaweiAdaptiveVolumeHandler(),
            OfbHuaweiBoxToneHandler(),
            OfbHuaweiHeadControlHandler(),
        ]
