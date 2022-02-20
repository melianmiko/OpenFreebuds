import os

from pystray import MenuItem, Menu

from openfreebuds_applet.l18n import t


def force_exit():
    # noinspection PyProtectedMember,PyUnresolvedReferences
    os._exit(0)


def get_quiting_menu():
    return [
        MenuItem(t("state_quiting"), None, enabled=False),
        MenuItem(t("action_kill_app"),
                 action=force_exit)
    ]


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
        MenuItem("Settings...",
                 action=get_settings_submenu(applet))
    ]


def get_settings_submenu(applet):
    items = [
        MenuItem(t("submenu_theme"),
                 action=get_theme_submenu(applet)),
        MenuItem(t("action_exit"),
                 action=lambda: applet.exit())
    ]

    return Menu(*items)


def get_theme_submenu(applet):
    current = applet.settings.theme

    items = [
        MenuItem(t("theme_auto"),
                 action=lambda: applet.set_theme("auto"),
                 checked=lambda _: current == "auto"),
        MenuItem(t("theme_light"),
                 action=lambda: applet.set_theme("light"),
                 checked=lambda _: current == "light"),
        MenuItem(t("theme_dark"),
                 action=lambda: applet.set_theme("dark"),
                 checked=lambda _: current == "dark")
    ]

    return Menu(*items)
