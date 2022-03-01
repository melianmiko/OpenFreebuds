import logging
import os
import webbrowser

import openfreebuds_backend
from pystray import MenuItem, Menu

from openfreebuds import event_bus
from openfreebuds.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import tools, tool_server, tool_actions, tool_update
from openfreebuds_applet.l18n import t, setup_language, setup_auto


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
    head = []

    # Build update menu item
    has_update, new_version = tool_update.get_result()
    if has_update:
        head.append(MenuItem(t("action_update").format(new_version),
                             action=tool_update.show_update_message))
        head.append(Menu.SEPARATOR)

    # Build device submenu
    device_items = [
        MenuItem(t("submenu_device_info"),
                 action=lambda: show_device_info(applet)),
        MenuItem(t("action_unpair"),
                 action=applet.drop_device)
    ]
    head.append(MenuItem(applet.settings.device_name, action=Menu(*device_items)))

    # Build connect/disconnect action
    if applet.manager.state == applet.manager.STATE_CONNECTED:
        action_connection_mgmt = MenuItem(t("action_disconnect"), action=applet.force_disconnect)
    else:
        action_connection_mgmt = MenuItem(t("action_connect"), action=applet.force_connect)
    head.append(action_connection_mgmt)

    # Ready
    head.append(Menu.SEPARATOR)
    return head


def get_app_menu_part(applet):
    version, _ = tools.get_version()

    items = [
        MenuItem("OpenFreebuds ({})".format(version),
                 action=lambda: webbrowser.open("https://melianmiko.ru/openfreebuds")),
        MenuItem(t("action_donate"),
                 action=lambda: webbrowser.open("https://melianmiko.ru/donate")),
        MenuItem("by MelianMiko", None, enabled=False),
        Menu.SEPARATOR
    ]

    add_startup_settings(applet, items)
    add_theme_select(applet, items)
    add_language_select(applet, items)
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

    return [
        MenuItem(t("submenu_app"),
                 action=Menu(*items))
    ]


def show_device_info(applet):
    if applet.manager.state != applet.manager.STATE_CONNECTED:
        openfreebuds_backend.show_message(t("mgr_state_2"), window_title=t("submenu_device_info"))
        return

    dev = applet.manager.device

    message = "{} ({})\n\n".format(applet.settings.device_name, applet.settings.address)
    message += "Model: {}\n".format(dev.get_property("device_model", "---"))
    message += "HW ver: {}\n".format(dev.get_property("device_ver", "---"))
    message += "FW ver: {}\n".format(dev.get_property("software_ver", "---"))
    message += "OTA ver: {}\n".format(dev.get_property("ota_version", "---"))
    message += "S/N: {}\n".format(dev.get_property("serial_number", "---"))
    message += "Headphone in: {}\n".format(dev.get_property("is_headphone_in", "---"))

    openfreebuds_backend.show_message(message, window_title=t("submenu_device_info"))


def toggle_hotkeys(applet):
    applet.settings.enable_hotkeys = not applet.settings.enable_hotkeys
    applet.settings.write()

    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


def toggle_show_update_dialog(applet):
    applet.settings.enable_update_dialog = not applet.settings.enable_update_dialog
    applet.settings.write()

    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


def toggle_flask(applet):
    applet.settings.enable_server = not applet.settings.enable_server
    applet.settings.write()

    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


def add_startup_settings(applet, items):
    run_at_boot = openfreebuds_backend.is_run_at_boot()
    show_update_dialog = applet.settings.enable_update_dialog

    items.append(MenuItem(t("option_show_update_dialog"),
                          action=lambda: toggle_show_update_dialog(applet),
                          checked=lambda _: show_update_dialog))

    items.append(MenuItem(t("option_run_at_boot"),
                          action=lambda: openfreebuds_backend.set_run_at_boot(not run_at_boot),
                          checked=lambda _: run_at_boot))


def add_hotkeys_settings(applet, items):
    settings = applet.settings
    config = settings.hotkeys_config
    all_actions = tool_actions.get_action_names()

    hotkey_items = [
        MenuItem(t("prop_enabled"),
                 action=lambda: toggle_hotkeys(applet),
                 checked=lambda _: settings.enable_hotkeys),
        Menu.SEPARATOR
    ]

    for a in all_actions:
        if a in config:
            add_hotkey_item(hotkey_items, applet, a, all_actions[a], config[a])
        else:
            add_hotkey_item(hotkey_items, applet, a, all_actions[a], "")

    hotkey_items += [
        Menu.SEPARATOR,
        MenuItem(t("notice_restart"), None, enabled=False)
    ]

    items.append(MenuItem(t("submenu_hotkeys"), Menu(*hotkey_items)))


def add_hotkey_item(items, applet, basename, pretty_name, current_value):
    if current_value != "":
        value = "Ctrl-Alt-" + current_value.upper()
    else:
        value = t("hotkey_disabled")

    text = pretty_name + " (" + value + ")"
    items.append(MenuItem(text, lambda: change_hotkey(basename, current_value, applet)))


def change_hotkey(basename, current_value, applet):
    openfreebuds_backend.ask_string(t("change_hotkey_message"),
                                    callback=lambda v: do_change_button(v, applet, basename),
                                    window_title=basename,
                                    current_value=current_value)


def do_change_button(new_value, applet, basename):
    if new_value is None:
        return

    new_value = new_value.lower()
    logging.debug("Set new hotkey for " + basename + " to value " + new_value)
    applet.settings.hotkeys_config[basename] = new_value
    applet.settings.write()

    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


def add_server_settings(applet, items):
    settings = applet.settings

    server_items = [
        MenuItem(t("prop_enabled"),
                 action=lambda: toggle_flask(applet),
                 checked=lambda _: settings.enable_server),
        Menu.SEPARATOR,
        MenuItem(t("webserver_port") + " " + str(tool_server.get_port()),
                 action=None,
                 enabled=False),
        MenuItem(t("notice_restart"), None, enabled=False)
    ]

    items.append(MenuItem(t("submenu_server"), Menu(*server_items)))


def add_theme_select(applet, items):
    current = applet.settings.theme

    theme_picker = [
        # MenuItem(t("submenu_theme"), None, enabled=False),
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

    items.append(MenuItem(t("submenu_theme"), Menu(*theme_picker)))


def add_language_select(applet, items):
    current = applet.settings.language
    variants = os.listdir(tools.get_assets_path() + "/locale")

    languages = [
        MenuItem("System",
                 action=lambda: set_language("", applet),
                 checked=lambda _: current == ""),
        Menu.SEPARATOR
    ]

    for a in variants:
        languages.append(create_lang_menu_item(a, applet))

    items.append(MenuItem(t("submenu_language"), Menu(*languages)))


def create_lang_menu_item(value, applet):
    current = applet.settings.language
    value = value.replace(".json", "")

    return MenuItem(value,
                    action=lambda: set_language(value, applet),
                    checked=lambda _: current == value)


def set_language(value, applet):
    applet.settings.language = value
    applet.settings.write()

    if value == "":
        setup_auto()
    else:
        setup_language(value)

    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)
