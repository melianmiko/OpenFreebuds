import threading
import tkinter
from tkinter import ttk

import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import http_server
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools, icons

PAD_X_BASE = 8
PAD_Y_BASE = 6
PAD_X_GROUP = 16
PAD_Y_GROUP = 12


def start(applet):
    def _int():
        SettingsBaseApp(applet).mainloop()

    threading.Thread(target=_int).start()


class SettingsBaseApp(tkinter.Tk):
    def __init__(self, applet):
        super().__init__()
        self.applet = applet
        tk_tools.apply_theme(self)

        self.wm_title(t("settings_title"))
        self.wm_resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self)
        frame.grid()

        notebook = ttk.Notebook(frame)
        notebook.grid(column=0, row=0, sticky="nesw")

        notebook.add(AppSettingsTab(notebook, self.applet),
                     text=t("settings_tab_app"))


class AppSettingsTab(ttk.Frame):
    THEME_OPTIONS = {
        "auto": t("theme_auto"),
        "light": t("theme_light"),
        "dark": t("theme_dark")
    }

    def __init__(self, root, applet):
        super().__init__(root)
        self.applet = applet
        self.settings = applet.settings     # type: SettingsStorage
        self.grid()

        self.var_run_at_boot = tkinter.BooleanVar(value=openfreebuds_backend.is_run_at_boot())
        self.var_show_update_dialog = tkinter.BooleanVar(value=self.settings.enable_update_dialog)
        self.var_compact_mode = tkinter.BooleanVar(value=self.settings.compact_menu)
        self.var_sleep_mode = tkinter.BooleanVar(value=self.settings.enable_sleep)
        self.var_debug_mode = tkinter.BooleanVar(value=self.settings.enable_debug_features)
        self.var_server = tkinter.BooleanVar(value=self.settings.enable_server)
        self.var_server_access = tkinter.BooleanVar(value=self.settings.server_access)
        self.var_theme = tkinter.StringVar(value=self.THEME_OPTIONS[self.settings.theme])
        self.var_icon_theme = tkinter.StringVar(value=self.THEME_OPTIONS[self.settings.icon_theme])

        # Ui Settings
        ui_root = ttk.Frame(self)
        ui_root.grid(column=0, row=0, padx=PAD_X_GROUP, pady=PAD_Y_GROUP, sticky="nesw")

        ttk.Label(ui_root, text=t("submenu_theme"))\
            .grid(column=0, row=0, sticky="nws", padx=PAD_X_BASE)
        c = ttk.Combobox(ui_root, values=list(self.THEME_OPTIONS.values()),
                         textvariable=self.var_theme, state="readonly")
        c.bind("<<ComboboxSelected>>", self._theme_changed)
        c.grid(column=1, row=0, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        ttk.Label(ui_root, text=t("submenu_icon_theme"))\
            .grid(column=0, row=1, sticky="nws", padx=PAD_X_BASE)
        c = ttk.Combobox(ui_root, values=list(self.THEME_OPTIONS.values()),
                         textvariable=self.var_icon_theme, state="readonly")
        c.bind("<<ComboboxSelected>>", self._icon_theme_changed)
        c.grid(column=1, row=1, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        # Main settings
        main_root = ttk.Labelframe(self, text=t("settings_group_main"))
        main_root.grid(column=0, row=1, padx=PAD_X_GROUP, pady=PAD_Y_GROUP, sticky="nesw")

        ttk.Checkbutton(main_root, text=t("option_run_at_boot"),
                        variable=self.var_run_at_boot,
                        command=self._toggle_run_at_boot)\
            .grid(column=0, row=0, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)
        ttk.Checkbutton(main_root, text=t("option_show_update_dialog"),
                        variable=self.var_show_update_dialog,
                        command=self._toggle_show_update_dialog)\
            .grid(column=0, row=1, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)
        ttk.Checkbutton(main_root, text=t("option_compact"),
                        variable=self.var_compact_mode,
                        command=self._toggle_compact_mode)\
            .grid(column=0, row=2, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        # HTTP server
        server_root = ttk.Labelframe(self, text=t("settings_group_server"))
        server_root.grid(column=0, row=2, padx=PAD_X_GROUP, pady=PAD_Y_GROUP, sticky="nesw")

        ttk.Checkbutton(server_root, text=t("option_server"),
                        variable=self.var_server,
                        command=self._toggle_server) \
            .grid(column=0, row=0, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)
        ttk.Checkbutton(server_root, text=t("prop_server_access"),
                        variable=self.var_server_access,
                        command=self._toggle_server_access) \
            .grid(column=0, row=1, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

        # Advanced
        adv_root = ttk.Labelframe(self, text=t("settings_group_advanced"))
        adv_root.grid(column=0, row=3, padx=PAD_X_GROUP, pady=PAD_Y_GROUP, sticky="nesw")

        ttk.Checkbutton(adv_root, text=t("option_sleep_mode"),
                        variable=self.var_sleep_mode,
                        command=self._toggle_sleep_mode) \
            .grid(column=0, row=0, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)
        ttk.Checkbutton(adv_root, text=t("option_debug_features"),
                        variable=self.var_debug_mode,
                        command=self._toggle_debug) \
            .grid(column=0, row=1, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE)

    def _toggle_run_at_boot(self):
        openfreebuds_backend.set_run_at_boot(self.var_run_at_boot.get())

    def _toggle_show_update_dialog(self):
        self.settings.enable_update_dialog = not self.settings.enable_update_dialog
        self.settings.write()

    def _toggle_compact_mode(self):
        self.settings.compact_menu = not self.settings.compact_menu
        self.settings.write()
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def _toggle_sleep_mode(self):
        self.settings.enable_sleep = not self.settings.enable_sleep
        self.settings.write()
        tk_tools.message(t("sleep_info"), "OpenFreebuds")

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
            tk_tools.confirm(t("server_global_warn"), "WARNING", self._do_toggle_access)
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

    def _do_toggle_access(self, result):
        if not result:
            self.var_server_access.set(result)
            return

        self.settings.server_access = not self.settings.server_access
        self.settings.write()
        http_server.start(self.applet)
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)
