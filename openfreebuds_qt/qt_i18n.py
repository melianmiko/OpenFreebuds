from PyQt6.QtWidgets import QApplication


def get_eq_preset_names():
    return {
        "equalizer_preset_default": QApplication.translate("EqPresetName", "Default"),
        "equalizer_preset_hardbass": QApplication.translate("EqPresetName", "Bass-boost"),
        "equalizer_preset_treble": QApplication.translate("EqPresetName", "Treble-boost"),
        "equalizer_preset_voices": QApplication.translate("EqPresetName", "Voices"),
    }
