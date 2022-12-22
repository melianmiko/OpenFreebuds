import tkinter
import logging
from tkinter import ttk

import openfreebuds_backend
from openfreebuds import device
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.modules import device_autoconfig
from openfreebuds_applet.ui import tk_tools
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage

log = logging.getLogger("DeviceSelectUI")


@tk_tools.ui_thread
def start(settings: SettingsStorage, manager: FreebudsManager):
    root = tkinter.Toplevel()
    root.wm_title("OpenFreebuds")
    root.wm_resizable(False, False)
    root.grid()

    tk_tools.setup_window(root)

    ttk.Label(root, text=t("first_run_message")) \
        .grid(sticky=tkinter.NW, columnspan=10, row=0, column=0, padx=16, pady=16)

    pane = ttk.Panedwindow(root, height=300)
    pane.grid(sticky=tkinter.NSEW, columnspan=10, row=1, column=0)

    frame = ttk.Frame(pane)
    pane.add(frame, weight=1)

    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    treeview = ttk.Treeview(
        frame,
        selectmode="browse",
        show="tree",
        yscrollcommand=scrollbar.set
    )
    scrollbar.config(command=treeview.yview)
    treeview.pack(expand=True, fill="both")

    status = ttk.Label(root, text=" ")
    status.grid(row=2, column=0, columnspan=10, pady=16, padx=16, sticky=tkinter.NW)

    # Connect selected device
    def on_confirm():
        iid = treeview.focus()
        values = treeview.item(iid)["values"]

        if values[0] == "pin":
            _, name, address = values
            if device.is_supported(name):
                apply_device(settings, manager, name, address)
            else:
                setup_manually_ui(address, settings, manager)
            root.destroy()
        elif values[0] == "custom":
            setup_manually_ui("", settings, manager)
            root.destroy()
        elif values[0] == "autoconfig":
            apply_device(settings, manager, "", "", autoconfig=True)
            root.destroy()

    # On select (update status row)
    def on_select(_):
        iid = treeview.focus()
        values = treeview.item(iid)["values"]
        if values[0] != "pin":
            status.config(text=" ")
            return
        status.config(text=t("address_prefix") + ": " + values[1])

    # Rebuild list
    # noinspection PyTypeChecker
    def rebuild_treeview():
        treeview.delete(*treeview.get_children())
        treeview.insert("", "end", text=t("device_autoconfig_mode"), values=("autoconfig", ))
        treeview.insert("", "end", iid=1, text=t("type_paired"), values=("none", ), open=True)

        # List paired
        paired = openfreebuds_backend.bt_list_devices()
        if len(paired) == 0:
            treeview.insert(1, "end", text=t("no_devices"), values=("none", ))
        for dev in paired:
            treeview.insert(1, "end", text=dev["name"], values=("pin", dev["name"], dev["address"]))
        
        # Add "manual" option
        treeview.insert("", "end", text=t("action_manual_connect"), values=("custom", ))

    rebuild_treeview()
    treeview.bind("<<TreeviewSelect>>", on_select)

    ttk.Button(root, text=t("connect"), style="Accent.TButton", command=on_confirm) \
        .grid(sticky=tkinter.NSEW, row=10, column=0, padx=16, pady=16)
    ttk.Button(root, text=t("refresh"), command=rebuild_treeview) \
        .grid(sticky=tkinter.NSEW, row=10, column=1, padx=0, pady=16)
    ttk.Button(root, text=t("cancel"), command=root.destroy) \
        .grid(sticky=tkinter.NSEW, row=10, column=2, padx=16, pady=16)
    
    root.mainloop()


@tk_tools.ui_thread
def setup_manually_ui(address, settings, manager):
    profiles = list(device.DEVICE_PROFILES.keys())

    root = tkinter.Toplevel()
    selected = tkinter.StringVar(value=profiles[0])
    address_var = tkinter.StringVar(value=address)
    root.wm_title(t("ui_manual_title"))
    root.wm_resizable(False, False)

    tk_tools.setup_window(root)

    def do_connect():
        root.destroy()
        apply_device(settings, manager, selected.get(), address_var.get())

    def do_close():
        start(settings, manager)
        root.destroy()

    frame = ttk.Frame(root)
    frame.grid()
    frame.grid_columnconfigure(2, weight=1)

    # Info
    info_id = "profile_select_message" if address != "" else "manual_device_setup_message"
    ttk.Label(frame, text=t(info_id))\
        .grid(columnspan=3, padx=16, pady=16, sticky=tkinter.NSEW)

    # Address input
    ttk.Label(frame, text=t("ui_manual_hint_address"))\
        .grid(row=1, columnspan=3, padx=16, pady=4, sticky=tkinter.NSEW)
    ttk.Entry(frame, state=("readonly" if address != "" else "normal"), textvariable=address_var)\
        .grid(row=2, columnspan=3, padx=16, pady=4, sticky=tkinter.NSEW)

    # Profile selector
    ttk.Label(frame, text=t("ui_manual_hint_profile"))\
        .grid(row=5, columnspan=3, padx=16, pady=4, sticky=tkinter.NSEW)
    ttk.Combobox(frame, state="readonly", values=profiles, textvariable=selected)\
        .grid(row=6, columnspan=3, padx=16, pady=4, stick=tkinter.NSEW)

    # Buttons
    ttk.Button(frame, text=t("connect"), command=do_connect, style="Accent.TButton")\
        .grid(row=10, sticky=tkinter.NW, padx=16, pady=12)
    ttk.Button(frame, text=t("cancel"), command=do_close) \
        .grid(row=10, column=1, sticky=tkinter.NW, pady=12)

    root.mainloop()


def apply_device(settings, manager, name, address, autoconfig=False):
    log.debug("Applying device {} {} autoconfig={}".format(name, address, autoconfig))
    settings.device_name = name
    settings.address = address
    settings.device_autoconfig = autoconfig
    settings.write()

    if address != "":
        manager.set_device(name, address)
    else:
        device_autoconfig.process(manager, settings)

    # tk_tools.message(t("welcome_tray_message"), "OpenFreebuds")
