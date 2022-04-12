import datetime
import hashlib
import logging
import os
import threading
import traceback

import openfreebuds_backend

current_tray_application = None


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
    processes = openfreebuds_backend.list_processes()

    for pid, name in processes:
        if ("openfreebuds" in name or "ofb_launcher" in name) and pid != our_pid:
            logging.debug("Found running instance PID=" + str(pid))
            return True

    return False


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


def safe_run_wrapper(func, display_name, _):
    async_with_ui(display_name)(func)()


def with_ui_exception(display_name):
    from openfreebuds_applet.ui import tk_tools

    def _wrapper(func):
        # noinspection PyUnresolvedReferences,PyProtectedMember,PyBroadException
        def _internal(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception:
                exc_text = traceback.format_exc()
                message = "An unhandled exception was caught in thread {}.\n\n{}"
                message = message.format(display_name, exc_text)
                logging.getLogger("RunSafe").exception("Action {} failed.".format(display_name))
                tk_tools.message(message, "OpenFreebuds", lambda: os._exit(1))
        return _internal
    return _wrapper


def async_with_ui(display_name):
    def _wrapper(func):
        def _thread(*args, **kwargs):
            with_ui_exception(display_name)(func)(*args, **kwargs)

        def _internal(*args, **kwargs):
            threading.Thread(target=_thread, args=args, kwargs=kwargs).start()
        return _internal
    return _wrapper
