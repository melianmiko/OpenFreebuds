import functools

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.constants import I18N_PATH

log = create_logger("OfbQtLocale")


@functools.cache
def list_available_locales():
    locales = []
    for file in I18N_PATH.iterdir():
        if file.name.endswith(".qm"):
            locales.append(file.name.split(".")[0])
    return locales
