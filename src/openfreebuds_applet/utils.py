import datetime
import hashlib
import logging
import os
import threading
import traceback

import openfreebuds_backend


def reverse_dict_props(obj):
    res = {}
    for a in obj:
        res[obj[a]] = a
    return res


def get_version():
    from version_info import VERSION
    return VERSION


def items_hash_string(items):
    hs = ""

    for a in items:
        hs += a.text + "," + str(a.checked) + str(a.radio) + \
            str(a.visible) + str(a.default) + str(a.enabled) + ","
        if a.submenu is not None:
            hs += items_hash_string(a.submenu.items)
        hs += ";"

    return hashlib.sha1(hs.encode("utf8")).hexdigest()


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


def get_app_storage_dir():
    path = openfreebuds_backend.get_app_storage_path() / "openfreebuds"
    if not path.is_dir():
        path.mkdir()
    return path


def safe_run_wrapper(func, display_name, _):
    return async_with_ui(display_name)(func)()


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
            thread = threading.Thread(target=_thread, args=args, kwargs=kwargs)
            thread.start()
            return thread
        return _internal
    return _wrapper
