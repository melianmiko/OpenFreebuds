import functools
from pathlib import Path

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.constants import I18N_PATH

log = create_logger("OfbQtLocale")
QT_BASE_PREFIX = "qtbase_"


@functools.cache
def list_available_locales():
    locales = []
    for file in I18N_PATH.iterdir():
        if file.name.endswith(".qm"):
            locales.append(file.name.split(".")[0])
    return locales


def list_qtbase_locales(translations_path: str) -> list[str]:
    """List Qt's own translation names, which use underscores (zh_CN, pt_BR)."""
    return [
        file.stem[len(QT_BASE_PREFIX):]
        for file in Path(translations_path).glob(f"{QT_BASE_PREFIX}*.qm")
    ]


def _normalize_locale(tag: str) -> str:
    """Normalize Qt/system locale tags so zh_CN, zh-CN and zh-Hans-CN can be compared."""
    return tag.replace("_", "-").lower()


def resolve_locale(requested: str, available: list[str]) -> str:
    """Pick the best available translation for a Qt locale tag.

    Qt returns underscore tags such as ``zh_CN`` while the shipped .qm files use
    ``zh-CN``; exact string matching therefore falls back to English even on a
    Chinese system. Match case/separator-insensitively, then by language prefix.
    """
    wanted = _normalize_locale(requested)
    for locale in available:
        if _normalize_locale(locale) == wanted:
            return locale

    language = wanted.split("-")[0]
    for locale in available:
        if _normalize_locale(locale) == language:
            return locale
    for locale in available:
        if _normalize_locale(locale).startswith(language + "-"):
            return locale

    for locale in available:
        if _normalize_locale(locale) == "en":
            return locale
    return available[0] if available else "en"
