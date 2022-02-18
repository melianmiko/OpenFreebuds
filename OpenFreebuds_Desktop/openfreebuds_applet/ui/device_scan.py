import logging
import threading

import pystray

from openfreebuds_applet.l18n import t

log = logging.getLogger("DeviceScanUI")


class State:
    device_selected = threading.Event()
    selected_device_name = None
    selected_device_address = None


def loop(applet):
    State.selected_device_name = None
    State.selected_device_address = None
    State.device_selected.clear()

    # TODO: Set icon

    while State.selected_device_address is None:
        # Applet exit check
        if applet.started is False:
            return

        # If state changed, leave
        if applet.manager.state != applet.manager.STATE_NO_DEV:
            return

        items = [pystray.MenuItem(text=t("select_device"),
                                  enabled=False,
                                  action=None)]

        for a in applet.manager.scan_results:
            items.append(_create_device_menu_item(a))

        applet.set_menu_items(items)

        applet.manager.list_paired()
        State.device_selected.wait(timeout=3)

    log.info("Selected device " + str(State.selected_device_address))

    # Save settings
    applet.settings.device_name = State.selected_device_name
    applet.settings.address = State.selected_device_address
    applet.settings.write()

    # Wait for device apply
    applet.manager.state_changed.clear()
    applet.manager.set_device(State.selected_device_address)
    applet.manager.state_changed.wait()


def _create_device_menu_item(data):
    address = data["address"]
    name = data["name"]

    def apply_device():
        State.selected_device_name = name
        State.selected_device_address = address
        State.device_selected.set()

    return pystray.MenuItem(text=name,
                            action=apply_device)
