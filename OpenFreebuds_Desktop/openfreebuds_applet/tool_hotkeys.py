import logging

import openfreebuds_backend

log = logging.getLogger("HotkeysTool")


class Data:
    applet = None


def start(applet):
    Data.applet = applet
    if not applet.settings.enable_hotkeys:
        return

    log.debug("Starting hotkey tool...")

    handlers = get_all_hotkeys()
    config = Data.applet.settings.hotkeys_config
    merged = {}

    for a in handlers:
        if a in config and config[a] != "":
            merged[config[a]] = handlers[a]

    openfreebuds_backend.bind_hotkeys(merged)
    log.debug("Started hotkey tool.")


def get_all_hotkeys():
    return {
        "next_mode": lambda *args: do_next_mode(),
        "mode_0": lambda *args: do_mode(0),
        "mode_1": lambda *args: do_mode(1),
        "mode_2": lambda *args: do_mode(2)
    }


def do_next_mode():
    dev = _get_device()
    if dev is not None:
        current = dev.get_property("noise_mode", -99)
        if current == -99:
            return
        next_mode = (current + 1) % 3
        dev.set_property("noise_mode", next_mode)
        log.debug("Switched to mode " + str(next_mode))


def do_mode(mode):
    dev = _get_device()
    if dev is not None:
        dev.set_property("noise_mode", mode)
        log.debug("Switched to mode " + str(mode))


def _get_device():
    manager = Data.applet.manager
    if manager.state != manager.STATE_CONNECTED:
        log.debug("Hotkey ignored, no device")
        return None

    return manager.device
