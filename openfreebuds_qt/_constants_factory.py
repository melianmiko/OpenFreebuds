import os
from pathlib import Path

import openfreebuds_backend


def get_assets_path() -> Path:
    assets_dir_name = "openfreebuds_assets"
    path = os.path.dirname(os.path.realpath(__file__))

    if os.path.isdir(path + "/" + assets_dir_name):
        return Path(path + "/" + assets_dir_name)
    elif os.path.isdir(path + "/../" + assets_dir_name):
        return Path(path + "/../" + assets_dir_name)
    elif os.path.isdir("/opt/openfreebuds/openfreebuds_assets"):
        return Path("/opt/openfreebuds/openfreebuds_assets")

    raise Exception("assets dir not found")


def get_app_storage_dir():
    path = openfreebuds_backend.get_app_storage_path() / "openfreebuds"
    if not path.is_dir():
        path.mkdir()
    return path
