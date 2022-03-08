import json
import locale
import logging
import os.path

from openfreebuds_applet import utils
from openfreebuds_applet.settings import SettingsStorage

lc_path = utils.get_assets_path() + "/locale/{}.json"
log = logging.getLogger("FreebudsLocale")

lang_names = {
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
    base_strings = {}


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

    with open(lc_path.format("en_US", encoding="utf-8"), "r") as f:
        Data.base_strings = json.loads(f.read())

    if langauge != "none":
        with open(lc_path.format(langauge), "r", encoding="utf-8") as f:
            Data.lang_strings = json.loads(f.read())


def ln(prop):
    prop = prop.replace("-", "_")
    if prop in lang_names:
        return lang_names[prop]

    return prop


def t(prop):
    if not Data.loaded:
        setup_auto()

    value = prop
    if prop in Data.lang_strings:
        value = Data.lang_strings[prop]
    elif prop in Data.base_strings:
        value = Data.base_strings[prop]
    else:
        log.warning("missing in base i18n: " + prop)

    return value
