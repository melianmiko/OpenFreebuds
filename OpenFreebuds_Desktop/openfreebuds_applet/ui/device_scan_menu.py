import logging

from openfreebuds_backend import Menu, MenuItem, bt_list_devices
from openfreebuds import event_bus
from openfreebuds_applet import icons
from openfreebuds_applet.l18n import t

log = logging.getLogger("DeviceScanUI")


def process(applet):
    # Set icon if required
    hashsum = "icon_offline"

    if applet.current_icon_hash != hashsum:
        icon = icons.get_icon_offline()
        applet.set_tray_icon(icon, hashsum)

    # Build menu
    devices = bt_list_devices()
    items = [
        MenuItem(text=t("select_device"),
                 enabled=False,
                 action=None)
    ]

    for a in devices:
        items.append(_create_device_menu_item(a, applet))

    items += [
        Menu.SEPARATOR,
        MenuItem(text=t("action_refresh_list"),
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

    return MenuItem(text=name,
                    action=apply_device)
