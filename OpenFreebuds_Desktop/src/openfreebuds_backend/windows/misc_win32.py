import os
import pathlib
import sys
import winreg

from pynput.keyboard import GlobalHotKeys


class _PynputState:
    current = None


def bind_hotkeys(keys):
    stop_hotkeys()

    # Add prefix to all keys
    x_keys = {}
    for a in keys:
        x_keys["<ctrl>+<alt>+" + a] = keys[a]

    _PynputState.current = GlobalHotKeys(x_keys)
    _PynputState.current.start()


def stop_hotkeys():
    if _PynputState.current is not None:
        _PynputState.current.stop()


def get_app_storage_path():
    return pathlib.Path.home() / "AppData/Roaming"


def open_in_file_manager(path):
    os.startfile(path)


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
            return


def get_system_id():
    return ["windows"]
