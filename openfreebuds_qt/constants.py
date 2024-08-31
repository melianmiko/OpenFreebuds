from openfreebuds_qt._constants_factory import get_assets_path, get_app_storage_dir

ASSETS_PATH = get_assets_path()
STORAGE_PATH = get_app_storage_dir()

IGNORED_LOG_TAGS = [
    "qasync._QEventLoop",
    "qasync.QThreadExecutor",
    "qasync._QThreadWorker",
]
