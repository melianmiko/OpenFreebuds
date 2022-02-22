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
    openfreebuds_backend.bind_hotkeys({
        "q": lambda _: do_next_mode()
    })
    log.debug("Started hotkey tool.")


def do_next_mode():
    dev = _get_device()
    if dev is not None:
        current = dev.get_property("noise_mode", -99)
        if current == -99:
            return
        next_mode = (current + 1) % 3
        dev.set_property("noise_mode", next_mode)
        log.debug("Switched to mode " + str(next_mode))


def _get_device():
    manager = Data.applet.manager
    if manager.state != manager.STATE_CONNECTED:
        log.debug("Hotkey ignored, no device")
        return None

    return manager.device
