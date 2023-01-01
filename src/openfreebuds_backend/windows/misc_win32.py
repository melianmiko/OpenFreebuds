import os
import pathlib
import re
import subprocess
import sys
import winreg

no_console = subprocess.STARTUPINFO()
no_console.dwFlags |= subprocess.STARTF_USESHOWWINDOW


def get_app_storage_path():
    return pathlib.Path.home() / "AppData/Roaming"


def open_in_file_manager(path):
    os.startfile(path)


def open_file(path):
    subprocess.Popen(["notepad.exe", path])


def is_running():
    """
    Check, is application already started.

    Will list OS processes and check for 'python -m openfreebuds'
    or 'openfreebuds' proc.
    """
    our_pid = os.getpid()

    cmd = "wmic process get description,processid"
    resp = re.sub(' +', ' ', subprocess.check_output(cmd, startupinfo=no_console).decode("utf8"))
    lines = resp.split("\r\r\n")[1:]
    for a in lines:
        a = a.split(" ", 1)
        try:
            pid = int(a[1])
            if pid == our_pid:
                continue

            cmdline = a[0]
            if "openfreebuds.exe" in cmdline:
                return True
        except (ValueError, IndexError):
            pass

    return False


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
