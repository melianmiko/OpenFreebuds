import logging
import os
import webbrowser

from mtrayapp import Menu

import openfreebuds_backend
from openfreebuds import event_bus, cli_io
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import utils
from openfreebuds_applet.modules import hotkeys, http_server, actions
from openfreebuds_applet.ui import icons, settings_ui
from openfreebuds_applet.l18n import t, setup_language, setup_auto, ln


class ApplicationMenuPart(Menu):
    """
    Base application settings menu part.
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet
        self.language_menu = LanguageMenu(applet)
        self.hotkeys_menu = HotkeysMenu(applet)

    def on_build(self):
        if not self.applet.settings.compact_menu:
            self.add_separator()

        self.add_submenu(t("submenu_language"), self.language_menu)
        self.add_submenu(t("submenu_hotkeys"), self.hotkeys_menu)
        self.add_separator()

        self.add_item(t("action_settings"), self.open_settings)
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

    def open_settings(self):
        settings_ui.start(self.applet)

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
        result = cli_io.dev_command(self.applet.manager.device, command)
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
