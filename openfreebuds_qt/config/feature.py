import os
import sys
from functools import cache

from PyQt6.QtWidgets import QSystemTrayIcon

from openfreebuds import APP_ROOT


class OfbQtFeatureAvailability:
    @staticmethod
    @cache
    def is_flatpak():
        return os.path.isfile("/app/is_container")

    @staticmethod
    @cache
    def is_portable():
        return (APP_ROOT / "is_portable").is_file()

    @staticmethod
    @cache
    def can_background():
        return QSystemTrayIcon.isSystemTrayAvailable()

    @staticmethod
    @cache
    def can_handle_hotkeys():
        return sys.platform != "linux" or os.environ.get("XDG_SESSION_TYPE", "") != "wayland"

    @staticmethod
    @cache
    def can_autostart():
        # Currently unused
        return not OfbQtFeatureAvailability.is_portable()

    @staticmethod
    @cache
    def can_autoupdate():
        return not OfbQtFeatureAvailability.is_portable() and sys.platform == "win32"
