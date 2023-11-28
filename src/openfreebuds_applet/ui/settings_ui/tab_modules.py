import tkinter
from collections import OrderedDict
from tkinter import ttk

from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import GenericModule
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools

PAD_X_BASE = 16
PAD_Y_BASE = 8


def toggle_module(mod: GenericModule):
    new_state = not mod.get_property("enabled", False)
    mod.set_property("enabled", new_state)

    if new_state:
        mod.start()
    else:
        mod.stop()


@tk_tools.ui_thread
def module_settings(mod: GenericModule):
    root = tkinter.Toplevel()
    root.wm_title(mod.name)
    root.geometry("450x550")
    root.wm_resizable(False, False)

    tk_tools.setup_window(root)

    frame = mod.make_settings_frame(root)
    frame.pack(fill=tkinter.BOTH)

    root.mainloop()


class ModulesSettingsTab(ttk.Frame):
    def __init__(self, parent, applet):
        super().__init__(parent)

        self.applet = applet
        self.settings = applet.settings  # type: SettingsStorage
        self.grid_columnconfigure(0, weight=1)

        self.vars = {}

        modules = self.applet.modules.modules  # type: dict[str, GenericModule]
        modules = OrderedDict(sorted(modules.items(), key=lambda row: row[1].order))
        for ident in modules:
            if modules[ident].hidden:
                continue
            self.add_item(modules[ident], ident)

    def add_item(self, mod: GenericModule, ident):
        self.vars[ident] = tkinter.BooleanVar(value=mod.get_property("enabled", False))

        fr = tkinter.Frame(self)
        fr.grid(column=0, padx=16, pady=4, sticky=tkinter.NW)
        fr.grid_columnconfigure(2, weight=1)

        enable_checkbox = ttk.Checkbutton(fr,
                                          variable=self.vars[ident],
                                          command=lambda: toggle_module(mod))
        enable_checkbox.grid(column=0, row=0, sticky=tkinter.NSEW)

        settings_btn = ttk.Button(fr,
                                  text=t("button_settings"),
                                  command=lambda: module_settings(mod),
                                  width=12)
        settings_btn.grid(column=1, row=0, sticky=tkinter.NSEW, padx=4)

        if mod.crashed:
            enable_checkbox.state(["disabled"])
            settings_btn.state(["disabled"])

        ttk.Label(fr,
                  text=mod.name) \
            .grid(column=2, row=0, sticky=tkinter.NSEW)

        info_fnt = tkinter.font.Font(size=10)
        ttk.Label(fr,
                  text=mod.description,
                  font=info_fnt) \
            .grid(column=0, row=1, sticky=tkinter.NW, pady=8, columnspan=3)
