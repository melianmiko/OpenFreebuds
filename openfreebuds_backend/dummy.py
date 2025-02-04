import logging
import os

log = logging.getLogger("OfbDummyBackend")

AUTOSTART_AVAILABLE = False
AUTOUPDATE_AVAILABLE = False
GLOBAL_HOTKEYS_AVAILABLE = False


def get_app_storage_path():
    return os.getcwd() + "/data"


def open_file(path):
    log.info("open_file " + path)


def is_run_at_boot():
    return False


async def set_run_at_boot(val):
    log.info("run_at_boot " + str(val))


async def bt_is_connected(address):
    log.info("is_connected " + address)
    return False


async def bt_connect(address):
    log.info("dummy_connect " + address)
    return False


async def bt_disconnect(address):
    log.info("dummy_disconnect " + address)
    return False


def bt_list_devices():
    return []


def is_dark_taskbar():
    return None
