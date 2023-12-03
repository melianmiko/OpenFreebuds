import threading
import tkinter.simpledialog

# noinspection PyUnresolvedReferences
from winsdk.windows.ui.viewmanagement import UISettings, UIColorType

from openfreebuds.logger import create_log

log = create_log("WindowsBackend")


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
