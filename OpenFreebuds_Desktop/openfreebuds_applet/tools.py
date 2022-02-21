import datetime
import hashlib
import os
import pathlib
import platform
import subprocess

import psutil as psutil


def items_hash_string(items):
    hs = ""

    for a in items:
        hs += a.text + "," + str(a.checked) + str(a.radio) + \
            str(a.visible) + str(a.default) + str(a.enabled) + ","
        if a.submenu is not None:
            hs += items_hash_string(a.submenu.items)
        hs += ";"

    return hashlib.sha1(hs.encode("utf8")).hexdigest()


def is_running():
    our_pid = os.getpid()

    for a in psutil.process_iter():
        if a.pid != our_pid:
            # Check base name
            if "openfreebuds" in a.name():
                return True

            # Check cmdline, eg 'python -m openfreebuds'
            try:
                for b in a.cmdline():
                    if "openfreebuds" in b:
                        return True
            except psutil.AccessDenied:
                pass

    return False


def get_assets_path():
    assets_dir_name = "openfreebuds_assets"
    path = os.path.dirname(os.path.realpath(__file__))

    if os.path.isdir(path + "/" + assets_dir_name):
        return path + "/" + assets_dir_name
    elif os.path.isdir(path + "/../" + assets_dir_name):
        return path + "/../" + assets_dir_name
    elif os.path.isdir("/usr/share/openfreebuds"):
        return "/usr/share/openfreebuds"

    raise Exception("assets dir not found")


def open_app_storage_dir():
    path = str(get_app_storage_dir())

    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Linux":
        subprocess.Popen(["xdg-open", path])
    else:
        raise Exception("Unknown platform name")


def get_app_storage_dir():
    home = pathlib.Path.home()

    if platform.system() == "Windows":
        path = home / "AppData/Roaming/openfreebuds"
    elif platform.system() == "Linux":
        path = home / ".config/openfreebuds"
    else:
        raise Exception("Unknown platform name")

    if not path.is_dir():
        path.mkdir()

    return path


def get_lock_file_path():
    path = get_app_storage_dir()
    return str(path / "lock.pid")


def get_settings_path():
    path = get_app_storage_dir()
    return str(path / "settings.json")


def get_log_filename():
    path = get_app_storage_dir()
    time_tag = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    return str(path / (time_tag + ".log"))
