import json
import locale
import logging
import os.path

from openfreebuds_applet import tools
from openfreebuds_applet.settings import SettingsStorage

lc_path = tools.get_assets_path() + "/locale/{}.json"
log = logging.getLogger("FreebudsLocale")


class Data:
    loaded = False
    current_language = "none"
    lang_strings = {}
    base_strings = {}


def _init():
    saved_language = SettingsStorage().language
    if saved_language != "" and os.path.isfile(lc_path.format(saved_language)):
        return _init_with(saved_language)

    user_language = locale.getlocale()[0]
    if os.path.isfile(lc_path.format(user_language)):
        return _init_with(user_language)

    return _init_with("none")


def _init_with(langauge):
    log.debug("Using language " + langauge)
    Data.current_language = langauge
    Data.loaded = True

    with open(lc_path.format("base"), "r") as f:
        Data.base_strings = json.loads(f.read())

    if langauge != "none":
        with open(lc_path.format(langauge), "r") as f:
            Data.lang_strings = json.loads(f.read())


def t(prop):
    if not Data.loaded:
        _init()

    if prop in Data.lang_strings:
        return Data.lang_strings[prop]

    if prop in Data.base_strings:
        return Data.base_strings[prop]

    log.warning("missing in base i18n: " + prop)
    return prop
