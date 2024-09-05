import openfreebuds_backend
from openfreebuds import APP_ROOT

ASSETS_PATH = APP_ROOT / "openfreebuds_qt" / "assets"
STORAGE_PATH = openfreebuds_backend.get_app_storage_path() / "openfreebuds"
I18N_PATH = APP_ROOT / "openfreebuds_qt" / "assets" / "i18n"

IGNORED_LOG_TAGS = [
    "qasync._QEventLoop",
    "qasync.QThreadExecutor",
    "qasync._QThreadWorker",
    "qasync._windows._EventWorker",
    "PIL.PngImagePlugin",
]

LINK_WEBSITE = "https://mmk.pw/en/openfreebuds/"
LINK_GITHUB = "https://github.com/melianmiko/OpenFreebuds/"
