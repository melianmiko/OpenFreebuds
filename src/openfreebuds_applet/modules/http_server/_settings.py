import tkinter
from tkinter import ttk

from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import GenericModule
from openfreebuds_applet.ui import tk_tools


class WebServerSettings(tkinter.Frame):
    def __init__(self, parent, module: GenericModule):
        super().__init__(parent)
        self.module = module
        self.grid_columnconfigure(0, weight=1)

        self.var_server_access = tkinter.BooleanVar(value=self.module.get_property("external_access", False))

        label_fnt = tkinter.font.Font(weight="bold")

        ttk.Label(self, text=t("settings_group_server"), font=label_fnt)\
            .grid(row=0, sticky="new", padx=16, pady=16)
        ttk.Checkbutton(self, text=t("prop_server_access"),
                        variable=self.var_server_access,
                        command=self._toggle_server_access) \
            .grid(row=1, sticky="new", padx=16, pady=8)
        ttk.Label(self, text=t("webserver_port") + " " + str(self.module.get_property("port"))) \
            .grid(row=2, sticky="new", padx=16, pady=8)
        ttk.Label(self, text=t("module_restart_required")) \
            .grid(row=3, sticky="new", padx=16, pady=8)

    def _toggle_server_access(self):
        if not self.module.get_property("external_access"):
            tk_tools.confirm(t("server_global_warn"), "WARNING",
                             self._do_toggle_access, self)
        else:
            self._do_toggle_access(True)

    def _do_toggle_access(self, result):
        if not result:
            self.var_server_access.set(result)
            return

        self.module.set_property("external_access", not self.module.get_property("external_access", False))
