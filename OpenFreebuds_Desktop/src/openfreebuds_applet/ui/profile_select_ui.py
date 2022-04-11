import tkinter
from tkinter import ttk

import openfreebuds.device
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import tk_tools


@tk_tools.ui_thread
def start(address, settings, manager):
    profiles = list(openfreebuds.device.DEVICE_PROFILES.keys())

    root = tkinter.Toplevel()
    selected = tkinter.StringVar(value=profiles[0])
    root.wm_title("OpenFreebuds")
    root.wm_resizable(False, False)

    def do_connect():
        root.destroy()
        settings.device_name = selected.get()
        settings.address = address
        settings.is_device_mocked = False
        settings.write()

        manager.set_device(selected.get(), address)

    frame = ttk.Frame(root)
    frame.grid()
    frame.grid_columnconfigure(2, weight=1)

    ttk.Label(frame, text=t("profile_select_message"))\
        .grid(columnspan=3, padx=16, pady=16, sticky=tkinter.NW)
    ttk.Combobox(frame, state="readonly", values=profiles, textvariable=selected)\
        .grid(row=1, columnspan=3, padx=16, pady=16, stick=tkinter.EW)

    ttk.Button(frame, text=t("connect"), command=do_connect, style="Accent.TButton")\
        .grid(row=2, sticky=tkinter.NW, padx=16, pady=12)
    ttk.Button(frame, text=t("cancel"), command=root.destroy) \
        .grid(row=2, column=1, sticky=tkinter.NW, pady=12)

    root.mainloop()
