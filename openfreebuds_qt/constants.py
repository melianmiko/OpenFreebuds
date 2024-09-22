from openfreebuds import APP_ROOT, STORAGE_PATH

ASSETS_PATH = APP_ROOT / "openfreebuds_qt" / "assets"
I18N_PATH = APP_ROOT / "openfreebuds_qt" / "assets" / "i18n"

IGNORED_LOG_TAGS = [
    "qasync._QEventLoop",
    "qasync.QThreadExecutor",
    "qasync._QThreadWorker",
    "qasync._windows._EventWorker",
    "PIL.PngImagePlugin",
]

LINK_WEBSITE = "https://mmk.pw/en/openfreebuds/"
LINK_WEBSITE_HELP = "https://mmk.pw/en/openfreebuds/help"
LINK_GITHUB = "https://github.com/melianmiko/OpenFreebuds/"
LINK_RPC_HELP = "http://localhost:19823/"
