import os
import sys
from functools import cache

from PyQt6.QtWidgets import QSystemTrayIcon

from openfreebuds import APP_ROOT, IS_PORTABLE


class OfbQtFeatureAvailability:
    @staticmethod
    @cache
    def is_flatpak():
        return os.path.isfile("/app/is_container")

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
        return not IS_PORTABLE

    @staticmethod
    @cache
    def can_autoupdate():
        return not IS_PORTABLE and sys.platform == "win32"
