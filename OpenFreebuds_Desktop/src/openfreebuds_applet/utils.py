import datetime
import hashlib
import logging
import os
import threading
import traceback

import psutil as psutil

import openfreebuds_backend


def get_version():
    from version_info import VERSION, DEBUG_MODE
    return VERSION, DEBUG_MODE


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
        name = _get_process_name_part(a)
        if "openfreebuds" in name and a.pid != our_pid:
            logging.debug("Found running instance PID=" + str(a.pid))
            return True

    return False


def _get_process_name_part(pr):
    if "python" in pr.name():
        try:
            cmd = pr.cmdline()
            if len(cmd) > 1:
                return cmd[1]
        except psutil.Error:
            pass

    return pr.name()


def get_assets_path():
    assets_dir_name = "openfreebuds_assets"
    path = os.path.dirname(os.path.realpath(__file__))

    if os.path.isdir(path + "/" + assets_dir_name):
        return path + "/" + assets_dir_name
    elif os.path.isdir(path + "/../" + assets_dir_name):
        return path + "/../" + assets_dir_name
    elif os.path.isdir("/opt/openfreebuds/openfreebuds_assets"):
        return "/opt/openfreebuds/openfreebuds_assets"

    raise Exception("assets dir not found")


def open_app_storage_dir():
    path = str(get_app_storage_dir())
    openfreebuds_backend.open_in_file_manager(path)


def get_app_storage_dir():
    path = openfreebuds_backend.get_app_storage_path() / "openfreebuds"
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


# noinspection PyBroadException,PyUnresolvedReferences
def run_safe(f, display_name, critical, args=None):
    message = "An unhandled exception was caught in thread {}.\n\n{}"
    if critical:
        message += "\nThis exception is critical. App will be closed."
    if args is None:
        args = []

    try:
        f(*args)
    except Exception:
        exc_text = traceback.format_exc()
        logging.getLogger("RunSafe").exception("Action {} failed.".format(display_name))
        openfreebuds_backend.show_message(message.format(display_name, exc_text))

        if critical:
            # noinspection PyProtectedMember
            os._exit(99)


def run_thread_safe(f, display_name, critical):
    t = threading.Thread(target=run_safe, args=(f, display_name, critical))
    t.start()

    return t
