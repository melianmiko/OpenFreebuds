import logging
import os
import time

log = logging.getLogger("DummyPlatform")


def get_app_storage_path():
    return os.getcwd() + "/data"


def open_in_file_manager(path):
    logging.info("open_dir " + path)


def bind_hotkeys(keys):
    logging.info(keys)


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


def get_system_id():
    return []


def show_message(message, callback=None, is_error=False):
    logging.info("msg " + message)
    logging.info(str(is_error))
    if callback:
        callback()


def ask_question(message, callback):
    logging.info("ask_question" + message)
    if callback:
        callback(False)


def ask_string(message, callback):
    logging.info("ask_str" + message)
    if callback:
        callback(None)


def ui_lock():
    while True:
        time.sleep(10)


def is_dark_theme():
    return False
