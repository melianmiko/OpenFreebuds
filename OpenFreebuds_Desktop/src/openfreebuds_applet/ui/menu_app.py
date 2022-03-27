import logging
import os
import webbrowser

from mtrayapp import Menu

import openfreebuds_backend
from openfreebuds import event_bus, cli_io
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import utils
from openfreebuds_applet.modules import hotkeys, http_server, actions
from openfreebuds_applet.ui import icons
from openfreebuds_applet.l18n import t, setup_language, setup_auto, ln


class ApplicationMenuPart(Menu):
    """
    Base application settings menu part.
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet
        self.theme_menu = ThemeMenu(applet)
        self.language_menu = LanguageMenu(applet)
        self.hotkeys_menu = HotkeysMenu(applet)
        self.base_settings_menu = SettingsMenu(applet)

    def on_build(self):
        if not self.applet.settings.compact_menu:
            self.add_separator()

        self.add_submenu(t("submenu_options"), self.base_settings_menu)
        self.add_submenu(t("submenu_theme"), self.theme_menu)
        self.add_submenu(t("submenu_language"), self.language_menu)
        self.add_submenu(t("submenu_hotkeys"), self.hotkeys_menu)
        self.add_separator()

        self.add_item(t("action_about"), self.about_dialog)
        self.add_item(t("action_open_appdata"), utils.open_app_storage_dir)
        self.add_separator()

        if self.applet.settings.enable_debug_features:
            self.add_item("DEV: Run command", self.do_command)
            self.add_item("DEV: Show logs", self.show_log)
            self.add_separator()

        self.add_item(t("action_exit"), self.applet.exit)

        if self.applet.settings.compact_menu:
            self.wrap(t("submenu_app"))

    def show_log(self):
        value = self.applet.log.getvalue()
        path = str(utils.get_app_storage_dir()) + "/last_log.txt"
        with open(path, "w") as f:
            f.write(value)

        openfreebuds_backend.open_file(path)

    def do_command(self):
        openfreebuds_backend.ask_string("openfreebuds>", self.on_command)

    def on_command(self, result):
        if result is None or result == "":
            return

        command = result.split(" ")
        result = cli_io.dev_command(self.applet.manager, command)
        self.application.message_box(result, "Dev mode")

    def about_dialog(self):
        version, debug = utils.get_version()

        message = "OpenFreebuds v{}\nBy MelianMiko\nLicensed under GPLv3\n".format(version)
        if debug:
            message += "DEBUG ENABLED\n"
        message += "\n" + t("message_open_website")

        self.application.confirm_box(message, "OpenFreebuds Desktop", self.about_callback)

    @staticmethod
    def about_callback(result):
        if result:
            webbrowser.open("https://melianmiko.ru/openfreebuds")


class ThemeMenu(Menu):
    """
    Icon theme select menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        current = self.applet.settings.theme

        for a in ["auto", "light", "dark"]:
            self.add_item(text=t("theme_" + a),
                          action=self.set_theme,
                          args=[a], checked=current == a)

    def set_theme(self, name):
        icons.set_theme(name)

        self.applet.settings.theme = name
        self.applet.settings.write()

        # Wipe hash for icon reload
        self.applet.current_icon_hash = ""

        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


class LanguageMenu(Menu):
    """
    Language select menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        current = self.applet.settings.language

        variants = os.listdir(utils.get_assets_path() + "/locale")
        variants.sort()

        self.add_item("System", self.on_auto, checked=current == "")
        self.add_separator()

        for lang in variants:
            lang = lang.replace(".json", "")
            self.add_item(ln(lang), self.on_select, args=[lang], checked=current == lang)

    def on_auto(self):
        self.applet.settings.language = ""
        self.applet.settings.write()

        setup_auto()
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def on_select(self, lang):
        self.applet.settings.language = lang
        self.applet.settings.write()

        setup_language(lang)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


class HotkeysMenu(Menu):
    """
    Language select menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        settings = self.applet.settings
        config = settings.hotkeys_config
        all_actions = actions.get_action_names()

        self.add_item(t("prop_enabled"),
                      action=self.do_enable_toggle,
                      checked=settings.enable_hotkeys)
        self.add_separator()

        for action_name in all_actions:
            value = t('hotkey_disabled')

            if action_name in config and config[action_name] != "":
                value = "Ctrl-Alt-" + config[action_name].upper()

            display_text = "{} ({})".format(all_actions[action_name], value)
            self.add_item(display_text,
                          self.on_hotkey_change,
                          args=[action_name])

    def on_hotkey_change(self, action_name):
        openfreebuds_backend.ask_string(t("change_hotkey_message"),
                                        callback=lambda value: self.do_change(action_name, value))

    def do_change(self, basename, new_value):
        if new_value is None:
            return

        new_value = new_value.lower()
        logging.debug("Set new hotkey for " + basename + " to value " + new_value)

        self.applet.settings.hotkeys_config[basename] = new_value
        self.applet.settings.write()
        hotkeys.start(self.applet)

        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def do_enable_toggle(self):
        self.applet.settings.enable_hotkeys = not self.applet.settings.enable_hotkeys
        self.applet.settings.write()

        hotkeys.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


class SettingsMenu(Menu):
    """
    Base app settings menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet
        self.settings = applet.settings

    def on_build(self):
        self.add_item(t("option_run_at_boot"), self.toggle_run_at_boot,
                      checked=openfreebuds_backend.is_run_at_boot())
        self.add_item(t("option_show_update_dialog"), self.toggle_update_dialog,
                      checked=self.settings.enable_update_dialog)
        self.add_item(t("option_compact"), self.toggle_compact,
                      checked=self.settings.compact_menu)
        self.add_separator()
        self.add_item(t("option_sleep_mode"), self.toggle_sleep,
                      checked=self.settings.enable_sleep)
        self.add_item(t("option_debug_features"), self.toggle_debug,
                      checked=self.settings.enable_debug_features)
        self.add_separator()
        self.add_item(t("option_server"), self.toggle_server,
                      checked=self.settings.enable_server)
        self.add_item(t("prop_server_access"), self.toggle_server_access,
                      checked=self.settings.server_access)
        self.add_item(t("webserver_port") + " " + str(http_server.get_port()),
                      enabled=False)

    def toggle_sleep(self):
        self.settings.enable_sleep = not self.settings.enable_sleep
        self.settings.write()
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)
        self.application.message_box(t("sleep_info"), "OpenFreebuds")

    def toggle_debug(self):
        self.settings.enable_debug_features = not self.settings.enable_debug_features
        self.settings.write()
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def toggle_compact(self):
        self.settings.compact_menu = not self.settings.compact_menu
        self.settings.write()
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def toggle_update_dialog(self):
        self.settings.enable_update_dialog = not self.settings.enable_update_dialog
        self.settings.write()
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    @staticmethod
    def toggle_run_at_boot():
        run_at_boot = openfreebuds_backend.is_run_at_boot()
        openfreebuds_backend.set_run_at_boot(not run_at_boot)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def toggle_server(self):
        self.settings.enable_server = not self.settings.enable_server
        self.settings.write()
        http_server.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def toggle_server_access(self):
        if not self.settings.server_access:
            self.application.confirm_box(t("server_global_warn"), "WARNING", self.do_toggle_access)
        else:
            self.do_toggle_access(True)

    def do_toggle_access(self, result):
        if not result:
            return

        self.settings.server_access = not self.settings.server_access
        self.settings.write()
        http_server.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)
