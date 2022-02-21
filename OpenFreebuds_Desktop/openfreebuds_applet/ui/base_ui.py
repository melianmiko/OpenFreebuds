import os

from pystray import MenuItem, Menu

from openfreebuds import event_bus
from openfreebuds_applet import tools, tool_server
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
    items = []

    add_theme_select(applet, items)
    items.append(Menu.SEPARATOR)
    add_hotkeys_settings(applet, items)
    add_server_settings(applet, items)

    items.extend([
        MenuItem(t("action_open_appdata"),
                 action=tools.open_app_storage_dir),
        Menu.SEPARATOR,
        MenuItem(t("action_exit"),
                 action=lambda: applet.exit())
    ])

    return Menu(*items)


def toggle_hotkeys(applet):
    applet.settings.enable_hotkeys = not applet.settings.enable_hotkeys
    applet.settings.write()

    event_bus.invoke("settings_changed")


def toggle_flask(applet):
    applet.settings.enable_flask = not applet.settings.enable_flask
    applet.settings.write()

    event_bus.invoke("settings_changed")


def add_hotkeys_settings(applet, items):
    settings = applet.settings

    hotkey_items = [
        MenuItem(t("prop_enabled"),
                 action=lambda: toggle_hotkeys(applet),
                 checked=lambda _: settings.enable_hotkeys),
        Menu.SEPARATOR,
        MenuItem(t("hotkey_next_mode") + ": " + settings.hotkey_next_mode,
                 action=None,
                 enabled=False),
        Menu.SEPARATOR,
        MenuItem(t("notice_restart"), None, enabled=False)
    ]

    items.append(MenuItem(t("submenu_hotkeys"), Menu(*hotkey_items)))


def add_server_settings(applet, items):
    settings = applet.settings

    server_items = [
        MenuItem(t("prop_enabled"),
                 action=lambda: toggle_flask(applet),
                 checked=lambda _: settings.enable_flask),
        Menu.SEPARATOR,
        MenuItem(t("webserver_port") + " " + str(tool_server.port),
                 action=None,
                 enabled=False),
        MenuItem(t("notice_restart"), None, enabled=False)
    ]

    items.append(MenuItem(t("submenu_server"), Menu(*server_items)))


def add_theme_select(applet, items):
    current = applet.settings.theme

    theme_picker = [
        MenuItem(t("submenu_theme"), None, enabled=False),
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

    items.extend(theme_picker)
