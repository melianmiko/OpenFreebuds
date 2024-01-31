import logging

import openfreebuds_backend
from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.logger import create_log
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import tk_tools

log = create_log("AppletActions")

# TODO: Refactor


def do_next_mode(manager):
    dev = _get_device(manager)       # type: BaseDevice
    if dev is not None:
        current = dev.find_property("anc", "mode")
        if current is None:
            return
        options = list(dev.find_property("anc", "mode_options").split(","))
        next_mode = options[(options.index(current) + 1) % len(options)]
        dev.set_property("anc", "mode", next_mode)
        log.debug("Switched to mode " + str(next_mode))
        return True

    return False


def do_mode(manager, mode):
    dev = _get_device(manager)       # type: BaseDevice

    if dev is not None:
        dev.set_property("anc", "mode", mode)
        log.debug("Switched to mode " + str(mode))
        return True

    return False


def _get_device(manager):
    if manager.state != manager.STATE_CONNECTED:
        log.debug("Hotkey ignored, no device")
        return None

    return manager.device


# @utils.async_with_ui("ForceConnect")
def do_connect(manager: FreebudsManager):
    if manager.state == manager.STATE_CONNECTED:
        return True

    if manager.state == manager.STATE_PAUSED:
        tk_tools.message(t("error_in_work"), "OpenFreebuds")
        return True

    manager.set_paused(True)
    log.debug("Trying to force connect device...")
    # noinspection PyBroadException
    try:
        if not openfreebuds_backend.bt_connect(manager.device_address):
            raise Exception("fail")
    except Exception:
        log.exception("Can't force connect device")
        tk_tools.message(t("error_force_action_fail"), "OpenFreebuds")

    log.debug("Finish force connecting")
    manager.set_paused(False)
    return True


def do_disconnect(manager):
    if manager.state == manager.STATE_PAUSED:
        tk_tools.message(t("error_in_work"), "OpenFreebuds")
        return False

    manager.set_paused(True)
    log.debug("Trying to force disconnect device...")
    # noinspection PyBroadException
    try:
        if not openfreebuds_backend.bt_disconnect(manager.device_address):
            raise Exception("fail")
    except Exception:
        log.exception("Can't disconnect device")
        tk_tools.message(t("error_force_action_fail"), "OpenFreebuds")

    log.debug("Finish force disconnecting")
    manager.set_paused(False)
    return True


def do_toggle_connected(manager: FreebudsManager):
    if manager.state == manager.STATE_CONNECTED:
        return do_disconnect(manager)
    else:
        return do_connect(manager)


def get_actions(manager: FreebudsManager):
    return {
        "next_mode": lambda *args: do_next_mode(manager),
        "mode_normal": lambda *args: do_mode(manager, "normal"),
        "mode_cancellation": lambda *args: do_mode(manager, "cancellation"),
        "mode_awareness": lambda *args: do_mode(manager, "awareness"),
        "connect": lambda *args: do_connect(manager),
        "disconnect": lambda *args: do_disconnect(manager),
        "toggle_connect": lambda *args: do_toggle_connected(manager)
    }


def get_action_names():
    return {
        "next_mode": t("action_next_mode"),
        "mode_normal": t("noise_mode_normal"),
        "mode_cancellation": t("noise_mode_cancellation"),
        "mode_awareness": t("noise_mode_awareness"),
        "connect": t("action_connect"),
        "disconnect": t("action_disconnect"),
        "toggle_connect": t("action_toggle_connection")
    }
