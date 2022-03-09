import logging

from openfreebuds.device.base import BaseDevice
from openfreebuds_applet.l18n import t

log = logging.getLogger("AppletActions")


def do_next_mode(applet):
    dev = _get_device(applet)       # type: BaseDevice
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


def do_mode(applet, mode):
    dev = _get_device(applet)       # type: BaseDevice
    if dev is not None:
        dev.set_property("anc", "mode", mode)
        log.debug("Switched to mode " + str(mode))
    else:
        return False


def _get_device(applet):
    if applet.manager.state != applet.manager.STATE_CONNECTED:
        log.debug("Hotkey ignored, no device")
        return None

    return applet.manager.device


def get_actions(applet):
    return {
        "next_mode": lambda *args: do_next_mode(applet),
        "mode_0": lambda *args: do_mode(applet, 0),
        "mode_1": lambda *args: do_mode(applet, 1),
        "mode_2": lambda *args: do_mode(applet, 2),
        "connect": lambda *args: applet.force_connect(),
        "disconnect": lambda *args: applet.force_disconnect(),
    }


def get_action_names():
    return {
        "next_mode": t("action_next_mode"),
        "mode_0": t("noise_mode_0"),
        "mode_1": t("noise_mode_1"),
        "mode_2": t("noise_mode_2"),
        "connect": t("action_connect"),
        "disconnect": t("action_disconnect")
    }