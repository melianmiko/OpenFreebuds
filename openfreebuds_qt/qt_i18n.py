from PyQt6.QtCore import QLocale
from PyQt6.QtWidgets import QApplication

from openfreebuds_qt.config import OfbQtConfigParser


def _ui_language_code() -> str:
    language = OfbQtConfigParser.get_instance().get("ui", "language", "auto")
    if language == "auto":
        language = QLocale.system().name()
    return language.split("_")[0].split("-")[0].lower()


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


def get_prompt_tone_name(entry, *, is_custom: bool) -> str:
    """界面统一出口：显示名。

    - 用户自定义条目：用户写什么就显示什么，任何语言下都不翻译；
    - 官方条目：中文读官方 config 的 zhCn，其它语言走 PromptToneName 翻译词典。
    """
    if is_custom:
        return entry.display_name or entry.name
    if _ui_language_code() == "zh":
        return entry.zh_cn or entry.name
    translated = QApplication.translate("PromptToneName", entry.name)
    return translated or entry.name
