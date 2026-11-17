from PyQt6.QtCore import QCoreApplication, QTranslator

from openfreebuds_qt.constants import I18N_PATH
from openfreebuds_qt.utils.i18n import resolve_locale


def test_system_underscore_locale_matches_hyphen_translation():
    available = ["de", "en", "zh-CN"]
    assert resolve_locale("zh_CN", available) == "zh-CN"
    assert resolve_locale("zh-Hans-CN", available) == "zh-CN"


def test_unknown_locale_falls_back_to_english():
    assert resolve_locale("fr_FR", ["de", "en", "zh-CN"]) == "en"


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
