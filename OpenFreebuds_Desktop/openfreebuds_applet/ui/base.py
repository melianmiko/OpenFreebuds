from pystray import MenuItem, Menu

from openfreebuds_applet.l18n import t


def get_full_menu_items(applet, items):
    return


def get_header_menu_part(applet):
    return [
        MenuItem(applet.settings.device_name, None, enabled=False),
        MenuItem(t("action_unpair"),
                 action=applet.drop_device),
        Menu.SEPARATOR
    ]


def get_app_menu_part(applet):
    return [
        Menu.SEPARATOR,
        MenuItem(t("action_exit"),
                 action=lambda: applet.exit())
    ]
