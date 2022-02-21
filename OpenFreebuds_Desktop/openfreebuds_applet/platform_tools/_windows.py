import ctypes
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.ui.viewmanagement import UISettings, UIColorType

RESULT_NO = 6
RESULT_YES = 7
MessageBox = ctypes.windll.user32.MessageBoxW


def show_message(message, window_title=""):
    MessageBox(None, message, window_title, 0)


def show_question(message, window_title=""):
    return MessageBox(None, message, window_title, 4)


def is_dark_theme():
    theme = UISettings()
    color_type = UIColorType.BACKGROUND
    color_value = theme.get_color_value(color_type)
    return color_value.r == 0
