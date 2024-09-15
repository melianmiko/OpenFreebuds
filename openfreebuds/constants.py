import os
import sys
from pathlib import Path


class OfbEventKind:
    STATE_CHANGED = "state_changed"
    DEVICE_CHANGED = "device_changed"
    PROPERTY_CHANGED = "prop_changed"
    QT_BRING_SETTINGS_UP = "qt::show_settings"
    QT_SETTINGS_CHANGED = "qt::settings_changed"


APP_ROOT = Path(os.path.dirname(os.path.realpath(__file__))).parent
