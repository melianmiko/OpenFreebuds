import logging
import os
import webbrowser

import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import tools, tool_server, tool_actions, tool_hotkeys, icons
from openfreebuds_applet.l18n import t, setup_language, setup_auto, ln
from openfreebuds_applet.wrapper.tray import TrayMenu


class ApplicationMenuPart(TrayMenu):
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
        self.add_item(t("action_open_appdata"), tools.open_app_storage_dir)
        self.add_separator()

        self.add_item(t("action_exit"), self.applet.exit)

        if self.applet.settings.compact_menu:
            self.wrap(t("submenu_app"))

    def about_dialog(self):
        version, debug = tools.get_version()

        message = "OpenFreebuds v{}\nBy MelianMiko\nLicensed under GPLv3\n".format(version)
        if debug:
            message += "DEBUG ENABLED\n"
        message += "\n" + t("message_open_website")

        openfreebuds_backend.ask_question(message, self.about_callback)

    @staticmethod
    def about_callback(result):
        if result:
            webbrowser.open("https://melianmiko.ru/openfreebuds")


class ThemeMenu(TrayMenu):
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


class LanguageMenu(TrayMenu):
    """
    Language select menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        current = self.applet.settings.language

        variants = os.listdir(tools.get_assets_path() + "/locale")
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


class HotkeysMenu(TrayMenu):
    """
    Language select menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        settings = self.applet.settings
        config = settings.hotkeys_config
        all_actions = tool_actions.get_action_names()

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
        tool_hotkeys.start(self.applet)

        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def do_enable_toggle(self):
        self.applet.settings.enable_hotkeys = not self.applet.settings.enable_hotkeys
        self.applet.settings.write()

        tool_hotkeys.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


class SettingsMenu(TrayMenu):
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
        self.add_item(t("option_server"), self.toggle_server,
                      checked=self.settings.enable_server)
        self.add_item(t("prop_server_access"), self.toggle_server_access,
                      checked=self.settings.server_access)
        self.add_item(t("webserver_port") + " " + str(tool_server.get_port()),
                      enabled=False)

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
        tool_server.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def toggle_server_access(self):
        if not self.settings.server_access:
            openfreebuds_backend.ask_question(t("server_global_warn"), self.do_toggle_access)
        else:
            self.do_toggle_access(True)

    def do_toggle_access(self, result):
        if not result:
            return

        self.settings.server_access = not self.settings.server_access
        self.settings.write()
        tool_server.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)
