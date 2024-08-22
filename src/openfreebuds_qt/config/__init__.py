from configparser import ConfigParser

import openfreebuds_backend
from openfreebuds_qt.constants import STORAGE_PATH


class _Data:
    instance: ConfigParser = None


def get_openfreebuds_qt_config():
    if _Data.instance is None:
        _Data.instance = ConfigParser()
        _Data.instance.read(STORAGE_PATH / "openfreebuds_qt.ini")
    return _Data.instance


def get_tray_icon_theme():
    config = get_openfreebuds_qt_config()
    value = config.get("theme", "tray_icon", fallback="auto")
    if value != "auto":
        return value
    return "dark" if openfreebuds_backend.is_dark_theme() else "light"
