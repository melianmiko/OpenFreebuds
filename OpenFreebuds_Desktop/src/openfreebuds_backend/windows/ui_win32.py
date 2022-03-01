import ctypes
import logging
import threading
import tkinter.simpledialog

# noinspection PyUnresolvedReferences
from winsdk.windows.ui.viewmanagement import UISettings, UIColorType

log = logging.getLogger("WindowsBackend")


def show_message(message, callback=None, is_error=False):
    msg_type = 0 if not is_error else 16

    def run_async():
        ctypes.windll.user32.MessageBoxW(None, message, "OpenFreebuds", msg_type)
        if callback:
            callback()
    threading.Thread(target=run_async).start()


def ask_question(message, callback):
    def run_async():
        result = ctypes.windll.user32.MessageBoxW(None, message, "OpenFreebuds", 4)
        callback(result == 6)
    threading.Thread(target=run_async).start()


# noinspection PyUnusedLocal
def ask_string(message, callback):
    def run_async():
        result = tkinter.simpledialog.askstring("OpenFreebuds", prompt=message)
        callback(result)
    threading.Thread(target=run_async).start()


def is_dark_theme():
    theme = UISettings()
    color_type = UIColorType.BACKGROUND
    color_value = theme.get_color_value(color_type)
    return color_value.r == 0
