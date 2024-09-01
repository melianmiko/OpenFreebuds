import os
from pathlib import Path

import openfreebuds_backend
from openfreebuds import APP_ROOT


def get_assets_path() -> Path:
    if (APP_ROOT / "openfreebuds_qt" / "assets").is_dir():
        return APP_ROOT / "openfreebuds_qt" / "assets"

    raise Exception("assets dir not found")


def get_app_storage_dir():
    path = openfreebuds_backend.get_app_storage_path() / "openfreebuds"
    if not path.is_dir():
        path.mkdir()
    return path
