import json
import locale
import logging
import os.path

from openfreebuds.logger import create_log
from openfreebuds_applet import utils
from openfreebuds_applet.settings import SettingsStorage

lc_path = utils.get_assets_path() + "/locale/{}.json"
log = create_log("FreebudsLocale")

available_langs = [
    "en_US",
    "ru_RU",
]

lang_names = {
    "": "Auto",
    "en_US": "English",
    "en_GB": "English (Britain)",
    "ru_RU": "Русский",
    "zh_CN": "Chinese"
}


class Data:
    loaded = False
    current_language = "none"
    charset = "utf8"
    lang_strings = {}


def setup_auto():
    saved_language = SettingsStorage().language
    if saved_language != "" and os.path.isfile(lc_path.format(saved_language)):
        return setup_language(saved_language)

    user_language = locale.getdefaultlocale()[0]
    if os.path.isfile(lc_path.format(user_language)):
        return setup_language(user_language)

    return setup_language("none")


def setup_language(langauge):
    log.debug("Using language " + langauge)
    Data.current_language = langauge
    Data.loaded = True
    Data.charset = locale.getdefaultlocale()[1]

    if langauge not in ["none", "en_US"]:
        with open(lc_path.format(langauge), "r", encoding="utf-8") as f:
            Data.lang_strings = json.loads(f.read())


def ln(prop):
    prop = prop.replace("-", "_")
    if prop in lang_names:
        return lang_names[prop]

    return prop


def list_langs():
    out = {"Auto": ""}
    for lang in available_langs:
        out[ln(lang)] = lang
    return out


def get_current_lang():
    return Data.current_language


def t(prop):
    if Data.current_language == "en_US":
        return prop
    if not Data.loaded:
        setup_auto()

    if prop in Data.lang_strings:
        value = Data.lang_strings[prop]
    else:
        value = prop

    return value
