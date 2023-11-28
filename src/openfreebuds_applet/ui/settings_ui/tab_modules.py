import tkinter
from tkinter import ttk

from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import GenericModule
from openfreebuds_applet.settings import SettingsStorage

PAD_X_BASE = 16
PAD_Y_BASE = 8


class ModulesSettingsTab(ttk.Frame):
    def __init__(self, parent, applet):
        super().__init__(parent)

        self.applet = applet
        self.settings = applet.settings  # type: SettingsStorage
        self.grid_columnconfigure(0, weight=1)

        self.vars = {}

        modules = self.applet.modules.modules  # type: dict[str, GenericModule]
        for ident in modules:
            self.add_item(modules[ident], ident)

    def add_item(self, mod: GenericModule, ident):
        self.vars[ident] = tkinter.BooleanVar(value=mod.get_property("enabled", False))

        fr = tkinter.Frame(self)
        fr.grid(column=0, padx=16, pady=8, sticky=tkinter.NW)
        fr.grid_columnconfigure(2, weight=1)

        ttk.Checkbutton(fr, variable=self.vars[ident],
                        command=lambda: self.toggle(mod)) \
            .grid(column=0, row=0, sticky=tkinter.NSEW)
        ttk.Button(fr, text=t("Settings"), width=12) \
            .grid(column=1, row=0, sticky=tkinter.NSEW, padx=4)
        ttk.Label(fr, text=mod.name) \
            .grid(column=2, row=0, sticky=tkinter.NSEW)
        ttk.Label(fr, text=mod.description) \
            .grid(column=0, row=1, sticky=tkinter.NW, pady=8, columnspan=3)

        # fr.grid_columnconfigure(1, minsize=120, weight=1)

    def toggle(self, mod: GenericModule):
        new_state = not mod.get_property("enabled", False)
        mod.set_property("enabled", new_state)

        if new_state:
            mod.start()
        else:
            mod.stop()

