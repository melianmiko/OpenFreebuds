import logging
import os

log = logging.getLogger("DummyPlatform")


def get_app_storage_path():
    return os.getcwd() + "/data"


def open_in_file_manager(path):
    logging.info("open_dir " + path)


def open_file(path):
    logging.info("open_file " + path)


def is_running():
    return False


def is_run_at_boot():
    return False


def set_run_at_boot(val):
    logging.info("run_at_boot " + str(val))


def bt_is_connected(address):
    logging.info("is_connected " + address)
    return False


def bt_device_exists(address):
    logging.info("exists " + address)
    return False


def bt_connect(address):
    log.info("dummy_connect " + address)
    return False


def bt_disconnect(address):
    log.info("dummy_disconnect " + address)
    return False


def bt_list_devices():
    return []


def ask_string(message, callback):
    logging.info("ask_str" + message)
    if callback:
        callback(None)


def is_dark_theme():
    return False
