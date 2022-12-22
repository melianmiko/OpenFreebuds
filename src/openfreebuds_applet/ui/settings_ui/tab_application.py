import tkinter
import webbrowser
from tkinter import ttk

import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t, list_langs, ln, setup_language, setup_auto
from openfreebuds_applet.modules import http_server
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools, icons

PAD_X_BASE = 16
PAD_Y_BASE = 4

LINK_TRANSLATE = "https://crowdin.com/project/openfreebuds"


class AppSettingsTab(ttk.Frame):
    LANGUAGE_OPTIONS = list_langs()
    THEME_OPTIONS = {
        "auto": t("theme_auto"),
        "light": t("theme_light"),
        "dark": t("theme_dark")
    }

    def __init__(self, parent, applet):
        super().__init__(parent)
        self.applet = applet
        self.settings = applet.settings     # type: SettingsStorage
        self.grid_columnconfigure(0, weight=1)

        self.var_run_at_boot = tkinter.BooleanVar(value=openfreebuds_backend.is_run_at_boot())
        self.var_show_update_dialog = tkinter.BooleanVar(value=self.settings.enable_update_dialog)
        self.var_sleep_mode = tkinter.BooleanVar(value=self.settings.enable_sleep)
        self.var_debug_mode = tkinter.BooleanVar(value=self.settings.enable_debug_features)
        self.var_server = tkinter.BooleanVar(value=self.settings.enable_server)
        self.var_server_access = tkinter.BooleanVar(value=self.settings.server_access)
        self.var_theme = tkinter.StringVar(value=self.THEME_OPTIONS[self.settings.theme])
        self.var_icon_theme = tkinter.StringVar(value=self.THEME_OPTIONS[self.settings.icon_theme])
        self.var_language = tkinter.StringVar(value=ln(self.settings.language))

        label_fnt = tkinter.font.Font(weight="bold")

        # Main settings
        ttk.Label(self, text=t("settings_group_main"), font=label_fnt)\
            .grid(row=1, pady=16, sticky=tkinter.NW, padx=PAD_X_BASE)
        main_root = ttk.Frame(self)
        main_root.grid(columnspan=2, row=2, sticky=tkinter.NSEW)
        main_root.grid_columnconfigure(0, weight=1)

        ttk.Label(main_root, text=t("submenu_language"))\
            .grid(column=0, row=0, sticky="nws", padx=PAD_X_BASE)
        c = ttk.Combobox(main_root, values=list(self.LANGUAGE_OPTIONS.keys()),
                         textvariable=self.var_language, state="readonly")
        c.bind("<<ComboboxSelected>>", self._language_changed)
        c.grid(column=1, row=0, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        ttk.Label(main_root, text=t("submenu_theme"))\
            .grid(column=0, row=1, sticky="nws", padx=PAD_X_BASE)
        c = ttk.Combobox(main_root, values=list(self.THEME_OPTIONS.values()),
                         textvariable=self.var_theme, state="readonly")
        c.bind("<<ComboboxSelected>>", self._theme_changed)
        c.grid(column=1, row=1, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        ttk.Label(main_root, text=t("submenu_icon_theme"))\
            .grid(column=0, row=2, sticky="nws", padx=PAD_X_BASE)
        c = ttk.Combobox(main_root, values=list(self.THEME_OPTIONS.values()),
                         textvariable=self.var_icon_theme, state="readonly")
        c.bind("<<ComboboxSelected>>", self._icon_theme_changed)
        c.grid(column=1, row=2, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        ttk.Checkbutton(main_root, text=t("option_run_at_boot"),
                        variable=self.var_run_at_boot,
                        command=self._toggle_run_at_boot)\
            .grid(column=0, row=3, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE, columnspan=2)
        ttk.Checkbutton(main_root, text=t("option_show_update_dialog"),
                        variable=self.var_show_update_dialog,
                        command=self._toggle_show_update_dialog)\
            .grid(column=0, row=4, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE, columnspan=2)

        link = ttk.Label(main_root, text=t("action_help_translate"), foreground="#04F", cursor="hand2")
        link.bind("<Button-1>", lambda: webbrowser.open(LINK_TRANSLATE))
        link.grid(row=5, columnspan=2, padx=PAD_X_BASE, pady=PAD_Y_BASE, sticky=tkinter.NW)

        # HTTP server
        ttk.Label(self, text=t("settings_group_server"), font=label_fnt)\
            .grid(row=3, pady=16, sticky=tkinter.NW, padx=PAD_X_BASE)
        ttk.Checkbutton(self, style="Switch.TCheckbutton",
                        variable=self.var_server,
                        command=self._toggle_server) \
            .grid(column=1, row=3, sticky="nse", padx=PAD_X_BASE)

        server_root = ttk.Frame(self)
        server_root.grid(columnspan=2, row=4, sticky=tkinter.NSEW)

        ttk.Checkbutton(server_root, text=t("prop_server_access"),
                        variable=self.var_server_access,
                        command=self._toggle_server_access) \
            .grid(column=0, row=0, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        ttk.Label(server_root, text=t("webserver_port") + " " + str(http_server.get_port())) \
            .grid(row=1, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        # Advanced
        ttk.Label(self, text=t("settings_group_advanced"), font=label_fnt)\
            .grid(row=5, pady=16, sticky=tkinter.NW, padx=PAD_X_BASE)
        adv_root = ttk.Frame(self)
        adv_root.grid(columnspan=2, row=6, sticky=tkinter.NSEW)

        ttk.Button(adv_root, text=t("action_open_appdata"), command=utils.open_app_storage_dir)\
            .grid(row=1, sticky=tkinter.NW, padx=PAD_X_BASE, pady=4)

    def _toggle_run_at_boot(self):
        openfreebuds_backend.set_run_at_boot(self.var_run_at_boot.get())

    def _toggle_show_update_dialog(self):
        self.settings.enable_update_dialog = not self.settings.enable_update_dialog
        self.settings.write()

    def _toggle_compact_mode(self):
        self.settings.compact_menu = not self.settings.compact_menu
        self.settings.write()
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def _toggle_debug(self):
        self.settings.enable_debug_features = not self.settings.enable_debug_features
        self.settings.write()
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def _toggle_server(self):
        self.settings.enable_server = not self.settings.enable_server
        self.settings.write()
        http_server.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def _toggle_server_access(self):
        if not self.settings.server_access:
            tk_tools.confirm(t("server_global_warn"), "WARNING",
                             self._do_toggle_access, self)
        else:
            self._do_toggle_access(True)

    def _get_theme_values(self):
        return dict((y, x) for x, y in self.THEME_OPTIONS.items())

    def _theme_changed(self, _):
        name = self._get_theme_values()[self.var_theme.get()]

        tk_tools.set_theme(name)
        self.settings.theme = name
        self.applet.settings.write()

    def _icon_theme_changed(self, _):
        name = self._get_theme_values()[self.var_icon_theme.get()]

        icons.set_theme(name)
        self.settings.icon_theme = name
        self.applet.settings.write()
        self.applet.current_icon_hash = ""
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def _language_changed(self, _):
        name = self.var_language.get()
        lang = self.LANGUAGE_OPTIONS[name]

        self.applet.settings.language = lang
        self.applet.settings.write()

        if lang == "":
            setup_auto()
        else:
            setup_language(lang)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def _do_toggle_access(self, result):
        if not result:
            self.var_server_access.set(result)
            return

        self.settings.server_access = not self.settings.server_access
        self.settings.write()
        http_server.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)
