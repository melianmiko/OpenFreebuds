import logging

import pystray

from openfreebuds_applet.l18n import t

log = logging.getLogger("DeviceScanUI")


def process(applet):
    items = [pystray.MenuItem(text=t("select_device"),
                              enabled=False,
                              action=None)]

    for a in applet.manager.scan_results:
        items.append(_create_device_menu_item(a, applet))

    applet.set_menu_items(items)
    applet.manager.list_paired()


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
