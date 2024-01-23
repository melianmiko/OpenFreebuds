import tkinter
from tkinter import ttk

import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet.l18n import t, list_langs, ln, setup_language, setup_auto
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools, icons
from openfreebuds_applet.ui.settings_ui.tab_modules import ModulesSettingsTab

PAD_X_BASE = 16
PAD_Y_BASE = 4


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

        ttk.Label(self, text=t("settings_tab_modules"), font=label_fnt)\
            .grid(row=3, pady=16, sticky=tkinter.NW, padx=PAD_X_BASE)
        ModulesSettingsTab(self, applet).grid(columnspan=2, row=4, sticky=tkinter.NSEW)

    def _toggle_run_at_boot(self):
        openfreebuds_backend.set_run_at_boot(self.var_run_at_boot.get())

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

