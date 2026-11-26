from PyQt6.QtCore import QCoreApplication

from openfreebuds.driver.huawei.device_catalog import color_name, describe_model

# Chinese color names as they appear in legacy values (cloud config v1 strings),
# mapped to the English marketing key used by the "DeviceColor" i18n context.
LEGACY_COLOR_ALIASES = {
    "白色": "White",
    "黑色": "Black",
    "蓝色": "Blue",
    "紫色": "Purple",
    "红色": "Red",
    "黄色": "Yellow",
    "绿色": "Green",
    "灰色": "Grey",
    "粉色": "Pink",
    "橙色": "Orange",
    "金色": "Gold",
    "银色": "Silver",
    "米色": "Beige",
    "卡其色": "Khaki",
    "浅紫色": "Light purple",
    "蓝紫色": "Blue-purple",
    "米白": "Off-white",
    "银白色": "Silver white",
    "星河蓝": "Starry blue",
    "红黄混色": "Red-yellow",
    "红蓝混色": "Red-blue",
    "蓝黄混色": "Blue-yellow",
    "黄红混色": "Yellow-red",
    "蓝红混色": "Blue-red",
    "黄蓝混色": "Yellow-blue",
}

# Internal Bluetooth aliases that should never reach the user-facing UI.
MODEL_NAME_ALIASES = {
    "dove": "HUAWEI FreeClip",
}


def translate_color_name(name: str) -> str:
    """
    Translate a color name (either an English marketing key or a legacy
    Chinese label) for the current UI language.
    """
    source = LEGACY_COLOR_ALIASES.get(name, name)
    translated = QCoreApplication.translate("DeviceColor", source)
    return translated or source


def color_name_for(model_id: str, code: str) -> str:
    """
    Localized marketing color name for a model/color code pair.
    Falls back to whatever the catalog returns when the code is unknown.
    """
    raw = color_name(model_id, code)
    if not raw:
        return ""
    return translate_color_name(raw)


def translate_model_name(name: str) -> str:
    """
    Translate a marketing model name for the current UI language.
    """
    if not name:
        return ""
    source = MODEL_NAME_ALIASES.get(name.casefold(), name)
    translated = QCoreApplication.translate("DeviceModel", source)
    return translated or source


def format_device_title(model_id: str, code: str, fallback: str) -> str:
    """Build the 'HUAWEI FreeClip 2 (Denim Blue)' style title. Chinese uses full-width brackets, other languages use ASCII brackets."""
    model = describe_model(model_id) if model_id else None
    base = translate_model_name(model) if model else fallback
    color = color_name_for(model_id, code) if code else ""

    if not color:
        return base

    lang = QCoreApplication.translate("DeviceColor", "LangTag") or ""
    full_width = lang.startswith("zh")
    return f"{base}（{color}）" if full_width else f"{base} ({color})"
