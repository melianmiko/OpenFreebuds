from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


PRO_5_EQ_PRESETS = {
    2: "bass",
    5: "default",
    9: "voice",
    13: "movie",
    14: "game",
    15: "podcast",
    16: "sports",
    17: "ai",
    18: "tchaikovsky_balance",
    19: "tchaikovsky_theatre",
    -55: "classical",
}

PRO_5_FEATURE_SWITCHES = {
    "adaptive_audio": 2,
    "voice_wakeup": 3,
    "smart_charge": 4,
    "alone_noise": 5,
    "head_control": HuaweiFeatureSwitchSpec(11, read_params=()),
    "conversation_awareness": 27,
    "charging_case_gesture": HuaweiFeatureSwitchSpec(34, write_payload_size=4),
    "earplug_type": HuaweiFeatureSwitchSpec(
        8,
        group="config",
        options={
            0: "type_0",
            1: "type_1",
            2: "type_2",
            3: "type_3",
        },
    ),
    "spatial_audio_mode": HuaweiFeatureSwitchSpec(
        24,
        group="sound",
        read_params=(2, 3),
        options={
            0: "off",
            1: "head_tracking",
            2: "fixed",
        },
    ),
    "spatial_audio_room": HuaweiFeatureSwitchSpec(
        24,
        group="sound",
        read_params=(2, 3),
        state_param=3,
        options={
            0: "default",
            1: "listen_book",
            2: "cinema",
            3: "music_hall",
        },
    ),
    "voice_control": HuaweiFeatureSwitchSpec(35, write_payload_size=4),
}

PRO_5_LONG_TAP_OPTIONS = {
    -1: "tap_action_off",
    0: "tap_action_assistant",
    10: "tap_action_switch_anc",
    15: "tap_action_short_audio",
}

PRO_5_LIGHT_LONG_TAP_OPTIONS = {
    -1: "tap_action_off",
    0: "tap_action_assistant",
    1: "tap_action_pause",
    2: "tap_action_next",
    3: "tap_action_switch_anc",
    4: "tap_action_short_audio",
    5: "tap_action_assistant",
    6: "tap_action_switch_anc",
}

PRO_5_LIGHT_TAP_CALL_OPTIONS = {
    -1: "tap_action_off",
    0: "tap_action_answer",
    1: "tap_action_end_call",
}

PRO_5_LIGHT_TAP_ONCE_OPTIONS = {
    -1: "tap_action_off",
    2: "tap_action_pause",
}

PRO_5_LIGHT_TAP_TWICE_OPTIONS = {
    -1: "tap_action_off",
    4: "tap_action_next",
}

PRO_5_LIGHT_TAP_THREE_OPTIONS = {
    -1: "tap_action_off",
    3: "tap_action_prev",
}

PRO_5_LIGHT_TAP_SPECS = [
    HuaweiLightTapSpec("light_tap_call_once", 0, 1, w_right=False, shared=True, options=PRO_5_LIGHT_TAP_CALL_OPTIONS),
    HuaweiLightTapSpec("light_tap_call_twice", 1, 1, w_right=False, shared=True, options=PRO_5_LIGHT_TAP_CALL_OPTIONS),
    HuaweiLightTapSpec("light_tap_once", 0, 2, w_right=False, shared=True, options=PRO_5_LIGHT_TAP_ONCE_OPTIONS),
    HuaweiLightTapSpec("light_tap_twice", 1, 2, w_right=False, shared=True, options=PRO_5_LIGHT_TAP_TWICE_OPTIONS),
    HuaweiLightTapSpec("light_tap_three", 2, 2, w_right=False, shared=True, options=PRO_5_LIGHT_TAP_THREE_OPTIONS),
    HuaweiLightTapSpec("light_long_tap", 3, 0, w_right=True, options=PRO_5_LIGHT_LONG_TAP_OPTIONS),
]


class OfbDriverHuaweiPro5(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds Pro 5
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiAncHandler(
                w_cancel_lvl=True,
                w_cancel_dynamic=True,
                w_voice_boost=True,
                awareness_level_options={
                    1: "voice_boost",
                    2: "standard_transparency",
                    4: "adaptive_transparency",
                },
            ),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiLogsHandler(),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiEqualizerPresetHandler(w_presets=PRO_5_EQ_PRESETS, w_custom=True),
            OfbHuaweiFeatureSwitchHandler(PRO_5_FEATURE_SWITCHES),
            OfbHuaweiConfigAutoPauseHandler(),
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiActionDoubleTapHandler(),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiActionLongTapSplitHandler(w_right=True, options_lt=PRO_5_LONG_TAP_OPTIONS),
            OfbHuaweiActionLightLongTapHandler(specs=PRO_5_LIGHT_TAP_SPECS),
            OfbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiFindDeviceHandler(),
            OfbHuaweiPromptToneHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(write_param=2),
        ]