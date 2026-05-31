from PyQt6.QtWidgets import QApplication


def get_anc_level_names():
    return {
        "comfort": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Comfortable"),
        "normal": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Normal"),
        "ultra": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Ultra"),
        "dynamic": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Dynamic"),
        "voice_boost": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Voice boost"),
        "standard_transparency": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Standard transparency"),
        "adaptive_transparency": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Adaptive transparency"),
    }


def get_eq_preset_names():
    return {
        "equalizer_preset_default": QApplication.translate("EqPresetName", "Default"),
        "equalizer_preset_hardbass": QApplication.translate("EqPresetName", "Bass-boost"),
        "equalizer_preset_treble": QApplication.translate("EqPresetName", "Treble-boost"),
        "equalizer_preset_voices": QApplication.translate("EqPresetName", "Voices"),
        "equalizer_preset_bass": QApplication.translate("EqPresetName", "Bass"),
        "equalizer_preset_voice": QApplication.translate("EqPresetName", "Voice"),
        "equalizer_preset_movie": QApplication.translate("EqPresetName", "Movie"),
        "equalizer_preset_game": QApplication.translate("EqPresetName", "Game"),
        "equalizer_preset_podcast": QApplication.translate("EqPresetName", "Podcast"),
        "equalizer_preset_sports": QApplication.translate("EqPresetName", "Sports"),
        "equalizer_preset_ai": QApplication.translate("EqPresetName", "AI"),
        "equalizer_preset_tchaikovsky_balance": QApplication.translate("EqPresetName", "Tchaikovsky Balance"),
        "equalizer_preset_tchaikovsky_theatre": QApplication.translate("EqPresetName", "Tchaikovsky Theatre"),
        "equalizer_preset_classical": QApplication.translate("EqPresetName", "Classical"),
        "equalizer_preset_symphony": QApplication.translate("EqPresetName", "Symphony"),
        "equalizer_preset_hi_fi_live": QApplication.translate("EqPresetName", "Hi-Fi Live"),
    }


def get_sound_toggle_names():
    return {
        "big_volume": QApplication.translate("OfbQtSoundQualityModule", "High volume"),
        "smart_call_volume": QApplication.translate("OfbQtSoundQualityModule", "Adaptive call volume"),
    }


def get_sound_option_names():
    return {
        "spatial_audio_mode": (
            QApplication.translate("OfbQtSoundQualityModule", "Spatial audio"),
            {
                "off": QApplication.translate("OfbQtSoundQualityModule", "Off"),
                "head_tracking": QApplication.translate("OfbQtSoundQualityModule", "Head tracking"),
                "fixed": QApplication.translate("OfbQtSoundQualityModule", "Fixed"),
            },
        ),
        "spatial_audio_room": (
            QApplication.translate("OfbQtSoundQualityModule", "Spatial room"),
            {
                "default": QApplication.translate("OfbQtSoundQualityModule", "Default"),
                "listen_book": QApplication.translate("OfbQtSoundQualityModule", "Book"),
                "cinema": QApplication.translate("OfbQtSoundQualityModule", "Cinema"),
                "music_hall": QApplication.translate("OfbQtSoundQualityModule", "Music hall"),
            },
        ),
    }


def get_device_feature_switch_names():
    return {
        "voice_wakeup": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Voice wake-up"),
        "voice_control": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Voice control"),
        "smart_charge": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Smart charge"),
        "alone_noise": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Alone noise reduction"),
        "head_control": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Head gesture control"),
        "charging_case_gesture": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Charging case gesture"),
        "left_right_ear_recognition": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Left/right ear recognition"),
    }


def get_device_adaptive_audio_names():
    return {
        "adaptive_audio": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Adaptive volume"),
        "conversation_awareness": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Conversation in headphones"),
    }


def get_device_config_option_names():
    return {
        "earplug_type": (
            QApplication.translate("OfbQtDeviceOtherSettingsModule", "Ear tip type"),
            {
                "type_0": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Type 0"),
                "type_1": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Type 1"),
                "type_2": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Type 2"),
                "type_3": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Type 3"),
            },
        ),
    }


def get_service_language_names():
    return {
        "en-GB": QApplication.translate("OfbQtDeviceOtherSettingsModule", "English (British)"),
        "zh-CN": QApplication.translate("OfbQtDeviceOtherSettingsModule", "Chinese"),
    }


def get_prompt_tone_names():
    return {
        "Unfold": QApplication.translate("PromptToneName", "Unfold"),
        "Whistle": QApplication.translate("PromptToneName", "Whistle"),
        "Bongo": QApplication.translate("PromptToneName", "Bongo"),
        "Chess": QApplication.translate("PromptToneName", "Chess"),
        "Dewdrop": QApplication.translate("PromptToneName", "Dewdrop"),
        "Doorbell": QApplication.translate("PromptToneName", "Doorbell"),
        "Drip": QApplication.translate("PromptToneName", "Drip"),
        "Fountain": QApplication.translate("PromptToneName", "Fountain"),
        "Huawei_Cascade": QApplication.translate("PromptToneName", "Huawei Cascade"),
        "Leap": QApplication.translate("PromptToneName", "Leap"),
        "Lit": QApplication.translate("PromptToneName", "Lit"),
        "Little_Wish": QApplication.translate("PromptToneName", "Little Wish"),
        "Meditation": QApplication.translate("PromptToneName", "Meditation"),
        "Pixies": QApplication.translate("PromptToneName", "Pixies"),
        "Play": QApplication.translate("PromptToneName", "Play"),
        "Pursue": QApplication.translate("PromptToneName", "Pursue"),
        "Rise": QApplication.translate("PromptToneName", "Rise"),
        "Shine": QApplication.translate("PromptToneName", "Shine"),
    }


def get_shortcut_names():
    return {
        "show_main_window": QApplication.translate("ShortcutName", "Show OpenFreebuds window"),
        "connect": QApplication.translate("ShortcutName", "Connect device"),
        "disconnect": QApplication.translate("ShortcutName", "Disconnect device"),
        "toggle_connect": QApplication.translate("ShortcutName", "Connect/disconnect device"),
        "next_mode": QApplication.translate("ShortcutName", "Next noise control mode"),
        "mode_normal": QApplication.translate("ShortcutName", "Disable noise control"),
        "mode_cancellation": QApplication.translate("ShortcutName", "Enable noise cancellation"),
        "mode_awareness": QApplication.translate("ShortcutName", "Enable awareness mode"),
        "enable_low_latency": QApplication.translate("ShortcutName", "Enable low-latency mode"),
    }
