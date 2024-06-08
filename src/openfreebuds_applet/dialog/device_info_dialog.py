import logging
import tkinter
from tkinter import ttk

from openfreebuds.device import BaseDevice
from openfreebuds.logger import create_log
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import tk_tools

log = create_log("FirstRun")


@tk_tools.ui_thread
def start(device: BaseDevice):
    root = tkinter.Toplevel(class_="openfreebuds")
    root.wm_title("Device info")
    root.geometry("500x400")
    root.wm_resizable(False, False)

    tk_tools.setup_window(root)

    table = ttk.Treeview(root, show="headings", columns=["p", "v"])
    table.grid(sticky=tkinter.NSEW)
    table.heading("p", text=t("Property"))
    table.heading("v", text=t("Value"))

    props = device.find_group("info")
    for key in props:
        value = props[key]
        table.insert("", tkinter.END, values=[key, value])

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    root.mainloop()
