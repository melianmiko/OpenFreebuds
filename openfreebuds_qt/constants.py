from openfreebuds import APP_ROOT
from openfreebuds_qt._constants_factory import get_assets_path, get_app_storage_dir

ASSETS_PATH = get_assets_path()
STORAGE_PATH = get_app_storage_dir()

I18N_PATH = APP_ROOT / "openfreebuds_qt" / "i18n"

IGNORED_LOG_TAGS = [
    "qasync._QEventLoop",
    "qasync.QThreadExecutor",
    "qasync._QThreadWorker",
    "qasync._windows._EventWorker",
]

LINK_WEBSITE = "https://mmk.pw/en/openfreebuds/"
LINK_GITHUB = "https://github.com/melianmiko/OpenFreebuds/"
