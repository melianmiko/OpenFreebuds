import os
import sys
from pathlib import Path

from openfreebuds_backend import get_app_storage_path


class OfbEventKind:
    STATE_CHANGED = "state_changed"
    DEVICE_CHANGED = "device_changed"
    PROPERTY_CHANGED = "prop_changed"
    QT_BRING_SETTINGS_UP = "qt::show_settings"
    QT_SETTINGS_CHANGED = "qt::settings_changed"


APP_ROOT = (
    Path(os.path.dirname(sys.executable))
    if getattr(sys, "frozen", False)
    else Path(os.path.dirname(os.path.realpath(__file__))).parent
)
IS_PORTABLE = (APP_ROOT / "is_portable").is_file() \
    or sys.executable.endswith("_portable.exe")
STORAGE_PATH = get_app_storage_path() / "openfreebuds"

if IS_PORTABLE:
    STORAGE_PATH = APP_ROOT / "data"

APP_ROOT = Path(os.path.dirname(os.path.realpath(__file__))).parent
