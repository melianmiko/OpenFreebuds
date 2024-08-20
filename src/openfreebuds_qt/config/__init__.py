from configparser import ConfigParser

from openfreebuds_qt.constants import STORAGE_PATH


class _Data:
    instance: ConfigParser = None


def get_openfreebuds_qt_config():
    if _Data.instance is None:
        _Data.instance = ConfigParser()
        _Data.instance.read(STORAGE_PATH / "openfreebuds_qt.ini")
    return _Data.instance
