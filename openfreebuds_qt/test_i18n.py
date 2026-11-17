import pytest
from PyQt6.QtCore import QCoreApplication, QTranslator

from openfreebuds_qt.constants import I18N_PATH
from openfreebuds_qt.utils.i18n import resolve_locale

SUPPORTED = ["de", "en", "es", "pt-BR", "ru", "tr_TR", "zh-CN"]


@pytest.mark.parametrize(("system_locale", "expected"), [
    ("zh_CN", "zh-CN"),
    ("zh-Hans-CN", "zh-CN"),
    ("de_DE", "de"),
    ("de_AT", "de"),
    ("es_ES", "es"),
    ("es_MX", "es"),
    ("pt_BR", "pt-BR"),
    ("pt_PT", "pt-BR"),
    ("ru_RU", "ru"),
    ("tr_TR", "tr_TR"),
    ("en_US", "en"),
    ("en_GB", "en"),
    ("fr_FR", "en"),
])
def test_system_locale_resolution(system_locale, expected):
    assert resolve_locale(system_locale, SUPPORTED) == expected


@pytest.mark.parametrize("locale", SUPPORTED)
def test_show_welcome_button_strings_are_translated(locale):
    expected = {
        "de": "Willkommensbildschirm anzeigen",
        "en": "Show welcome screen",
        "es": "Mostrar pantalla de bienvenida",
        "pt-BR": "Mostrar tela de boas-vindas",
        "ru": "Показать экран приветствия",
        "tr_TR": "Karşılama ekranını göster",
        "zh-CN": "显示欢迎界面",
    }

    app = QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load(str(I18N_PATH / f"{locale}.qm"))
    app.installTranslator(translator)
    try:
        assert translator.translate("OfbQtUiSettingsModule", "Show welcome screen") == expected[locale]
    finally:
        app.removeTranslator(translator)


def test_first_run_dialog_strings_are_translated():
    app = QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load(str(I18N_PATH / "zh-CN.qm"))
    app.installTranslator(translator)
    try:
        assert translator.translate("OfbQtFirstRunDialog", "Welcome") == "欢迎"
        assert translator.translate("OfbQtFirstRunDialog", "Get started") == "开始使用"
    finally:
        app.removeTranslator(translator)
