import logging

from pystray import Menu, MenuItem

import openfreebuds_backend
from openfreebuds import event_bus, device_names
from openfreebuds.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import icons
from openfreebuds_applet.l18n import t
from openfreebuds_backend import bt_list_devices

log = logging.getLogger("DeviceScanUI")
devices = bt_list_devices()


def process(applet):
    # Build menu
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
    global devices
    devices = bt_list_devices()
    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


def _create_device_menu_item(data, applet):
    address = data["address"]
    name = data["name"]

    def apply_device():
        if not device_names.is_supported(name):
            ui_response = openfreebuds_backend.ask_question(t("question_not_supported"), "Openfreebuds")
            if ui_response == openfreebuds_backend.UI_RESULT_NO:
                return

        applet.manager.set_device(address)

        applet.settings.device_name = name
        applet.settings.address = address
        applet.settings.write()

    return MenuItem(text=name,
                    action=apply_device)
