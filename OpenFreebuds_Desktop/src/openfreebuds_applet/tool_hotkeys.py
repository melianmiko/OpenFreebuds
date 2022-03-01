import logging

import openfreebuds_backend
from openfreebuds_applet import tool_actions

log = logging.getLogger("HotkeysTool")


def start(applet):
    openfreebuds_backend.stop_hotkeys()

    if not applet.settings.enable_hotkeys:
        return

    log.debug("Starting hotkey tool...")

    handlers = tool_actions.get_actions(applet)
    config = applet.settings.hotkeys_config
    merged = {}

    for a in handlers:
        if a in config and config[a] != "":
            merged[config[a]] = handlers[a]

    openfreebuds_backend.bind_hotkeys(merged)
    log.debug("Started hotkey tool.")
