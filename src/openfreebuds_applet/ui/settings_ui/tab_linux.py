import tkinter
from tkinter import ttk

from openfreebuds_applet.modules import mpris_helper
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.l18n import t

PAD_X_BASE = 16
PAD_Y_BASE = 8


class LinuxSettingsTab(ttk.Frame):
    def __init__(self, parent, applet):
        super().__init__(parent)
        self.applet = applet
        self.settings = applet.settings     # type: SettingsStorage
        self.grid_columnconfigure(0, weight=1)

        self.var_mpris_helper = tkinter.BooleanVar(value=self.settings.enable_mpris_helper)
        ttk.Checkbutton(self, text=t("option_mpris_helper"),
                        variable=self.var_mpris_helper,
                        command=self._toggle_mpris)\
            .grid(column=0, row=0, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE, columnspan=2)

        ttk.Label(self, text=t("option_mpris_helper_guide"))\
            .grid(column=0, row=1, sticky=tkinter.NW, padx=PAD_X_BASE, pady=PAD_Y_BASE, columnspan=2)

    def _toggle_mpris(self):
        self.settings.enable_mpris_helper = self.var_mpris_helper.get()
        self.settings.write()

        mpris_helper.start(self.applet)
