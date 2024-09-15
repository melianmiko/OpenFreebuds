from PyQt6.QtWidgets import QApplication


def get_eq_preset_names():
    return {
        "equalizer_preset_default": QApplication.translate("EqPresetName", "Default"),
        "equalizer_preset_hardbass": QApplication.translate("EqPresetName", "Bass-boost"),
        "equalizer_preset_treble": QApplication.translate("EqPresetName", "Treble-boost"),
        "equalizer_preset_voices": QApplication.translate("EqPresetName", "Voices"),
    }


def get_shortcut_names():
    return {
        "connect": QApplication.translate("ShortcutName", "Connect device"),
        "disconnect": QApplication.translate("ShortcutName", "Disconnect device"),
        "toggle_connect": QApplication.translate("ShortcutName", "Connect/disconnect device"),
        "next_mode": QApplication.translate("ShortcutName", "Next noise control mode"),
        "mode_normal": QApplication.translate("ShortcutName", "Disable noise control"),
        "mode_cancellation": QApplication.translate("ShortcutName", "Enable noise cancellation"),
        "mode_awareness": QApplication.translate("ShortcutName", "Enable awareness mode"),
        "enable_low_latency": QApplication.translate("ShortcutName", "Enable low-latency mode"),
    }
