import logging
import threading
import tkinter.simpledialog
import winreg

# noinspection PyUnresolvedReferences
from winsdk.windows.ui.viewmanagement import UISettings, UIColorType

log = logging.getLogger("OfbWindowsBackend")


# noinspection PyUnusedLocal
def ask_string(message, callback):
    def run_async():
        result = tkinter.simpledialog.askstring("OpenFreebuds", prompt=message)
        callback(result)
    threading.Thread(target=run_async).start()


def is_dark_taskbar():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
    ) as key:
        try:
            value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
            return value == 0
        except (FileNotFoundError, OSError):
            return False
