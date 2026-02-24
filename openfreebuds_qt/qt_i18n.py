from PyQt6.QtWidgets import QApplication


def get_anc_level_names():
    return {
        "comfort": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Comfortable"),
        "normal": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Normal"),
        "ultra": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Ultra"),
        "dynamic": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Dynamic"),
        "voice_boost": QApplication.translate("OfbDeviceAncLevelTrayMenu", "Voice boost"),
    }


def get_eq_preset_names():
    return {
        "equalizer_preset_default": QApplication.translate("EqPresetName", "Default"),
        "equalizer_preset_hardbass": QApplication.translate("EqPresetName", "Bass-boost"),
        "equalizer_preset_treble": QApplication.translate("EqPresetName", "Treble-boost"),
        "equalizer_preset_voices": QApplication.translate("EqPresetName", "Voices"),
        "equalizer_preset_dynamic": QApplication.translate("EqPresetName", "Dynamic"),
        "equalizer_preset_symphony": QApplication.translate("EqPresetName", "Symphony"),
        "equalizer_preset_hi_fi_live": QApplication.translate("EqPresetName", "Hi-Fi Live"),
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
