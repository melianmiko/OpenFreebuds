import pytest
from PyQt6.QtCore import QCoreApplication, QLibraryInfo, QTranslator

from openfreebuds_qt.constants import I18N_PATH
from openfreebuds_qt.utils.i18n import list_qtbase_locales, resolve_locale

SUPPORTED = ["de", "en", "es", "pt-BR", "ru", "tr_TR", "zh-CN"]
QT_TRANSLATIONS_PATH = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)


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


@pytest.mark.parametrize(("app_locale", "qt_locale"), [
    ("de", "de"),
    ("en", "en"),
    ("es", "es"),
    ("pt-BR", "pt_BR"),
    ("ru", "ru"),
    ("tr_TR", "tr"),
    ("zh-CN", "zh_CN"),
])
def test_qtbase_locale_uses_qt_file_names(app_locale, qt_locale):
    available = list_qtbase_locales(QT_TRANSLATIONS_PATH)
    assert qt_locale in available
    assert resolve_locale(app_locale, available) == qt_locale


def test_qtbase_translates_standard_text_control_menu():
    app = QCoreApplication.instance() or QCoreApplication([])
    available = list_qtbase_locales(QT_TRANSLATIONS_PATH)
    qt_locale = resolve_locale("zh-CN", available)
    translator = QTranslator()
    assert translator.load(f"qtbase_{qt_locale}", QT_TRANSLATIONS_PATH)
    app.installTranslator(translator)
    try:
        translated = translator.translate("QWidgetTextControl", "Copy &Link Location")
        assert translated
        assert "链接" in translated
        assert translator.translate("QWidgetTextControl", "Select All") == "全选"
    finally:
        app.removeTranslator(translator)


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


@pytest.mark.parametrize("locale", SUPPORTED)
def test_tone_import_and_drop_alert_strings_are_translated(locale):
    expected = {
        "de": ("ZIP importieren", "Sturz-Warnung", "Importiert: {0}, übersprungen: {1}, fehlgeschlagen: {2}."),
        "en": ("Import ZIP", "Drop alert", "Imported {0}, skipped {1}, failed {2}."),
        "es": ("Importar ZIP", "Alerta de caída", "Importados: {0}, omitidos: {1}, fallidos: {2}."),
        "pt-BR": ("Importar ZIP", "Alerta de queda", "Importados: {0}, ignorados: {1}, falharam: {2}."),
        "ru": ("Импортировать ZIP", "Оповещение о падении", "Импортировано: {0}, пропущено: {1}, ошибок: {2}."),
        "tr_TR": ("ZIP içe aktar", "Düşme uyarısı", "İçe aktarılan: {0}, atlanan: {1}, başarısız: {2}."),
        "zh-CN": ("导入 ZIP", "掉落提示", "已导入 {0} 个，跳过 {1} 个，失败 {2} 个。"),
    }

    app = QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load(str(I18N_PATH / f"{locale}.qm"))
    app.installTranslator(translator)
    try:
        assert translator.translate("OfbQtDeviceOtherSettingsModule", "Import ZIP") == expected[locale][0]
        assert translator.translate("OfbQtDeviceOtherSettingsModule", "Drop alert") == expected[locale][1]
        assert translator.translate(
            "OfbQtDeviceOtherSettingsModule",
            "Imported {0}, skipped {1}, failed {2}.",
        ) == expected[locale][2]
    finally:
        app.removeTranslator(translator)


@pytest.mark.parametrize("locale", SUPPORTED)
def test_pro_5_gesture_strings_are_translated(locale):
    expected = {
        "de": ("Einmal zusammendrücken", "Zusammengedrückt halten",
               "Anruf annehmen/beenden", "Anruf ablehnen", "Geräuschkontrolle"),
        "en": ("Pinch once", "Pinch & hold", "Answer/end call", "Reject call", "Noise control"),
        "es": ("Pellizcar una vez", "Pellizcar y mantener",
               "Responder/finalizar llamada", "Rechazar llamada", "Control de ruido"),
        "pt-BR": ("Apertar uma vez", "Apertar e manter",
                  "Atender/encerrar chamada", "Rejeitar chamada", "Controle de ruído"),
        "ru": ("Сжатие один раз", "Сжатие и удержание",
               "Ответ на вызов/завершение вызова", "Отклонение вызова", "Контроль уровня шума"),
        "tr_TR": ("Bir kez sıkıştır", "Sıkıştır ve basılı tut",
                  "Arama yanıtla/sonlandır", "Arama reddet", "Gürültü kontrolü"),
        "zh-CN": ("按捏一下", "捏住", "接听/挂断电话", "拒接来电", "噪声控制"),
    }

    app = QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load(str(I18N_PATH / f"{locale}.qm"))
    app.installTranslator(translator)
    try:
        sources = ("Pinch once", "Pinch & hold", "Answer/end call", "Reject call", "Noise control")
        for source, translation in zip(sources, expected[locale]):
            assert translator.translate("OfbQtGesturesModule", source) == translation

        labels = (
            "Pinch once",
            "Pinch once in call",
            "Pinch twice",
            "Pinch twice in call",
            "Pinch three times",
            "Pinch & hold",
        )
        for source in labels:
            translation = translator.translate("OfbQtGesturesModule", source)
            assert translation
            if locale != "en":
                assert translation != source
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
