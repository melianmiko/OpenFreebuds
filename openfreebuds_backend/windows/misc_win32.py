import subprocess
import sys
import winreg
from pathlib import Path

# Portable mode if file name ends with `_portable.exe`
# or location folder contains `is_portable` flag-file.
IS_PORTABLE = sys.executable.endswith("_portable.exe") \
              or (Path(sys.executable).parent / "is_portable").is_file()

# Feature flags
AUTOSTART_AVAILABLE = not IS_PORTABLE
AUTOUPDATE_AVAILABLE = not IS_PORTABLE          # TODO: mmk_updater add portable replace support
GLOBAL_HOTKEYS_AVAILABLE = True

no_console = subprocess.STARTUPINFO()
no_console.dwFlags |= subprocess.STARTF_USESHOWWINDOW


def get_app_storage_path():
    # In portable mode, store all app-related data near executable
    if IS_PORTABLE:
        return Path(sys.executable).parent / "data"

    return Path.home() / "AppData" / "Roaming" / "openfreebuds"


def open_file(path):
    subprocess.Popen(["notepad.exe", path])


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


async def set_run_at_boot(val):
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
