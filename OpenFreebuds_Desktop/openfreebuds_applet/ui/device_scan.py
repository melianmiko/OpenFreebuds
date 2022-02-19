import logging

import pystray

from openfreebuds import system_io, event_bus
from openfreebuds_applet.l18n import t

log = logging.getLogger("DeviceScanUI")


def process(applet):
    devices = system_io.list_paired()
    items = [
        pystray.MenuItem(text=t("select_device"),
                         enabled=False,
                         action=None)
    ]

    for a in devices:
        items.append(_create_device_menu_item(a, applet))

    items += [
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(text=t("action_refresh_list"),
                         action=send_update_request)
    ]

    applet.set_menu_items(items)


def send_update_request():
    event_bus.invoke("ui_update")


def _create_device_menu_item(data, applet):
    address = data["address"]
    name = data["name"]

    def apply_device():
        applet.manager.set_device(address)

        applet.settings.device_name = name
        applet.settings.address = address
        applet.settings.write()

    return pystray.MenuItem(text=name,
                            action=apply_device)
