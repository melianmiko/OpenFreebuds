import logging
import tkinter

from tkinter import ttk

import openfreebuds_backend
from openfreebuds.logger import create_log
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools
from openfreebuds_applet.dialog import device_select

log = create_log("FirstRun")


@tk_tools.ui_thread
def show(settings: SettingsStorage, manager: FreebudsManager):
    root = tkinter.Toplevel(class_="openfreebuds")
    root.wm_title("Welcome")
    root.wm_resizable(False, False)

    tk_tools.setup_window(root)

    var_run_at_boot = tkinter.BooleanVar(value=True)
    var_config = tkinter.BooleanVar(value=False)

    def finish():
        root.destroy()

        settings.first_run = False
        settings.write()

        if var_run_at_boot.get():
            openfreebuds_backend.set_run_at_boot(True)
        if var_config.get():
            device_select.start(settings, manager)

    ttk.Label(root,
              text=t("Welcome,\n\n"
                     "This application allows you to manage your HUAWEI FreeBuds. "
                     "There's no main window, app just provide a tray indicator, "
                     "which you can find on taskbar near other indicators. "
                     "Right-click them to see a list of options.\n\n"
                     "Device will be selected automatically, "
                     "but you can override it. Here's some common "
                     "settings, you can change it anytime from "
                     "settings menu:\n"),
              wraplength=500)\
        .pack(padx=12, pady=12, expand=True)

    ttk.Checkbutton(root, text=t("Run application on boot"), variable=var_run_at_boot) \
        .pack(padx=12, pady=4, anchor=tkinter.NW)
    ttk.Checkbutton(root, text=t("Configure device manually"), variable=var_config) \
        .pack(anchor=tkinter.NW, padx=12, pady=4)
    ttk.Button(root, text=t("Begin"), style="Accent.TButton", command=finish) \
        .pack(anchor=tkinter.NE, padx=12, pady=12)

    root.mainloop()
