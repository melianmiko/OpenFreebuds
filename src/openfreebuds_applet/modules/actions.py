import logging

import openfreebuds_backend
from openfreebuds.device import HuaweiSPPDevice
from openfreebuds.device.base import BaseDevice
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import tk_tools

log = logging.getLogger("AppletActions")


def do_next_mode(manager):
    dev = _get_device(manager)       # type: BaseDevice
    if dev is not None:
        current = dev.find_property("anc", "mode", -99)
        if current == -99:
            return
        next_mode = (current + 1) % 3
        dev.set_property("anc", "mode", next_mode)
        log.debug("Switched to mode " + str(next_mode))
        return True
    else:
        return False


def do_mode(manager, mode):
    dev = _get_device(manager)       # type: BaseDevice
    if dev is not None:
        dev.set_property("anc", "mode", mode)
        log.debug("Switched to mode " + str(mode))
    else:
        return False


def _get_device(manager):
    if manager.state != manager.STATE_CONNECTED:
        log.debug("Hotkey ignored, no device")
        return None

    return manager.device


# @utils.async_with_ui("ForceConnect")
def do_connect(manager: FreebudsManager):
    if manager.state == manager.STATE_CONNECTED:
        return

    if manager.state == manager.STATE_PAUSED:
        tk_tools.message(t("error_in_work"), "OpenFreebuds")
        return

    manager.set_paused(True)
    log.debug("Trying to force connect device...")
    # noinspection PyBroadException
    try:
        spp = HuaweiSPPDevice(manager.device_address)
        if not spp.request_interaction():
            log.debug("Can't interact via SPP, try to connect anyway...")

        if not openfreebuds_backend.bt_connect(manager.device_address):
            raise Exception("fail")
    except Exception:
        log.exception("Can't force connect device")
        tk_tools.message(t("error_force_action_fail"), "OpenFreebuds")

    log.debug("Finish force connecting")
    manager.set_paused(False)


def do_disconnect(manager):
    if manager.state == manager.STATE_PAUSED:
        tk_tools.message(t("error_in_work"), "OpenFreebuds")
        return

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


def do_toggle_connected(manager: FreebudsManager):
    if manager.state == manager.STATE_CONNECTED:
        return do_disconnect(manager)
    else:
        return do_connect(manager)


def get_actions(manager: FreebudsManager):
    return {
        "next_mode": lambda *args: do_next_mode(manager),
        "mode_0": lambda *args: do_mode(manager, 0),
        "mode_1": lambda *args: do_mode(manager, 1),
        "mode_2": lambda *args: do_mode(manager, 2),
        "connect": lambda *args: do_connect(manager),
        "disconnect": lambda *args: do_disconnect(manager),
        "toggle_connect": lambda *args: do_toggle_connected(manager)
    }


def get_action_names():
    return {
        "next_mode": t("action_next_mode"),
        "mode_0": t("noise_mode_0"),
        "mode_1": t("noise_mode_1"),
        "mode_2": t("noise_mode_2"),
        "connect": t("action_connect"),
        "disconnect": t("action_disconnect"),
        "toggle_connect": t("action_toggle_connection")
    }
