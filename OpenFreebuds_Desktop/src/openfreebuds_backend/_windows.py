import asyncio
import ctypes
import logging
import os
import pathlib
import subprocess
import sys
import winreg
import tkinter.simpledialog

from openfreebuds_backend.utils import windows_utils

UI_RESULT_NO = 7
UI_RESULT_YES = 6

log = logging.getLogger("WindowsBackend")


def get_app_storage_path():
    return pathlib.Path.home() / "AppData/Roaming"


def open_in_file_manager(path):
    os.startfile(path)


def bind_hotkeys(keys):
    x_keys = {}
    for a in keys:
        x_keys["<ctrl>+<alt>+" + a] = keys[a]

    from pynput.keyboard import GlobalHotKeys
    GlobalHotKeys(x_keys).start()


def is_run_at_boot():
    with winreg.OpenKey(
            key=winreg.HKEY_CURRENT_USER,
            sub_key=r'Software\Microsoft\Windows\CurrentVersion\Run',
            reserved=0,
            access=winreg.KEY_ALL_ACCESS,
    ) as key:
        idx = 0
        while idx < 1_000:     # Max 1.000 values
            try:
                key_name, _, _ = winreg.EnumValue(key, idx)
                if key_name == "openfreebuds":
                    return True
                idx += 1
            except OSError:
                break
    return False


def set_run_at_boot(val):
    with winreg.OpenKey(
            key=winreg.HKEY_CURRENT_USER,
            sub_key=r'Software\Microsoft\Windows\CurrentVersion\Run',
            reserved=0,
            access=winreg.KEY_ALL_ACCESS,
    ) as key:
        try:
            if val:
                winreg.SetValueEx(key, "openfreebuds", 0, winreg.REG_SZ, sys.executable)
            else:
                winreg.DeleteValue(key, "openfreebuds")
        except OSError:
            return False
    return True


def bt_is_connected(address):
    return asyncio.run(windows_utils.win_is_bt_device_connected(address))


def bt_connect(address):
    if not windows_utils.tools_ready():
        return False

    base_args = [windows_utils.extra_tools_dir + "\\btcom.exe",  "-b\"{}\"".format(address)]

    try:
        subprocess.check_output(base_args + ["-r", "-s111e"])
        subprocess.check_output(base_args + ["-c", "-s111e"])
        subprocess.check_output(base_args + ["-r", "-s110b"])
        subprocess.check_output(base_args + ["-c", "-s110b"])
        return True
    except subprocess.CalledProcessError:
        return False


def bt_disconnect(address):
    if not windows_utils.tools_ready():
        return False

    base_args = [windows_utils.extra_tools_dir + "\\btcom.exe",  "-b\"{}\"".format(address)]

    try:
        subprocess.check_output(base_args + ["-r", "-s111e"])
        subprocess.check_output(base_args + ["-r", "-s110b"])
        return True
    except subprocess.CalledProcessError:
        return False


def bt_device_exists(address):
    devices = bt_list_devices()

    for a in devices:
        if a["address"] == address:
            return True

    return False


def bt_list_devices():
    return asyncio.run(windows_utils.win_list_bt_devices())


def get_system_id():
    return ["windows"]


def show_message(message, window_title="", is_error=False):
    msg_type = 0
    if is_error:
        msg_type = 16

    ctypes.windll.user32.MessageBoxW(None, message, window_title, msg_type)


def ask_question(message, window_title=""):
    return ctypes.windll.user32.MessageBoxW(None, message, window_title, 4)


# noinspection PyUnusedLocal
def ask_string(message, window_title="", current_value=""):
    return tkinter.simpledialog.askstring(window_title, prompt=message)


def is_dark_theme():
    return windows_utils.win_is_dark()
