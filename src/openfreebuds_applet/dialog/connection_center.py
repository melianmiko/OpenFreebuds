import tkinter
from tkinter import ttk

from openfreebuds.device import BaseDevice
from openfreebuds.device.huawei.tools import reverse_dict
from openfreebuds.logger import create_log
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import tk_tools

log = create_log("ConnCenter")


class ConnCenter(tkinter.Toplevel):
    def __init__(self, device: BaseDevice):
        super().__init__()

        self.btn_unpair = None
        self.cb_auto_connect = None
        self.btn_connect = None
        self.device_name_view = None
        self.devices_table = None
        self.preferred_device_picker = None

        self.var_main_toggle = tkinter.BooleanVar(value=device.find_property("config", "dual_connect"))
        self.var_preferred_device = tkinter.StringVar(value="")
        self.var_auto_connect = tkinter.BooleanVar(value=False)

        self.device_names = {}
        self.selected_device_addr = None
        self.y = 0

        self.device = device

    def init(self):
        self.wm_title("Connection center")
        self.geometry("420x500")
        self.wm_resizable(False, False)
        self.grid_columnconfigure(0, weight=1)
        tk_tools.setup_window(self)

        self.add_global_toggle()
        self.add_preferred_device_select()
        self.add_device_management_table()
        self.add_device_management_actions()

        self.refresh()
        self.mainloop()

    def refresh(self):
        preferred_device_mac = self.device.find_property("config", "preferred_device")
        # Wipe
        self.devices_table.delete(*self.devices_table.get_children())
        self.device_names = {
            t("preferred_device_auto_config"): "0" * 12,
        }

        # Iterate and add
        for mac_addr, name in self.device.find_group("dev_name").items():
            full_name = f"{name} ({mac_addr})"
            self.device_names[full_name] = mac_addr
            self.devices_table.insert("", "end", text=name, values=("m" + mac_addr,))

        self.preferred_device_picker.config(values=list(self.device_names.keys()))
        self.var_preferred_device.set(reverse_dict(self.device_names)[preferred_device_mac])

    def add_global_toggle(self):
        box = ttk.Frame(self)
        box.grid(row=self.y, column=0, sticky=tkinter.NSEW)
        box.grid_columnconfigure(0, weight=1)
        self.y += 1

        label_fnt = tkinter.font.Font(weight="bold")
        ttk.Label(box, text=t("toggle_dual_connect"), font=label_fnt) \
            .grid(row=0, column=0, pady=16, sticky=tkinter.NSEW, padx=16)
        ttk.Checkbutton(box, variable=self.var_main_toggle,
                        style="Switch.TCheckbutton",
                        command=self.on_main_toggle) \
            .grid(row=0, column=1, padx=16, pady=4)

    def add_preferred_device_select(self):
        ttk.Label(self, text=t("text_preferred_device_guide"), wraplength=420 - 32) \
            .grid(row=self.y, column=0, pady=8, sticky=tkinter.NSEW, padx=16)

        box = ttk.Frame(self)
        box.grid(row=self.y + 1, column=0, sticky=tkinter.NSEW)
        box.grid_columnconfigure(0, weight=1)
        self.y += 2

        ttk.Label(box, text=t("select_preferred_device")) \
            .grid(column=0, row=0, sticky="nws", padx=16, pady=4)
        self.preferred_device_picker = ttk.Combobox(box,
                                                    values=list(self.device_names.keys()),
                                                    textvariable=self.var_preferred_device,
                                                    state="readonly")
        self.preferred_device_picker.bind("<<ComboboxSelected>>", self.on_preferred_device_select)
        self.preferred_device_picker.grid(column=1, row=0, sticky=tkinter.NW, padx=16, pady=4)

    def add_device_management_table(self):
        ttk.Label(self, text=t("text_device_table_guide")) \
            .grid(row=self.y, column=0, pady=8, sticky=tkinter.NSEW, padx=16)

        pane = ttk.Panedwindow(self, height=300)
        pane.grid(sticky=tkinter.NSEW, row=self.y + 1, column=0, padx=16, pady=8)
        self.grid_rowconfigure(self.y + 1, weight=1)
        self.y += 2

        # Table
        frame = ttk.Frame(pane)
        pane.add(frame, weight=1)
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        self.devices_table = ttk.Treeview(frame, selectmode="browse", show="tree", yscrollcommand=scrollbar.set)
        self.devices_table.bind("<<TreeviewSelect>>", self.on_device_select)
        self.devices_table.pack(expand=True, fill="both")
        scrollbar.config(command=self.devices_table.yview)

    def add_device_management_actions(self):
        box = ttk.Frame(self)
        box.grid(row=self.y, column=0, sticky=tkinter.NSEW, padx=8)
        box.grid_columnconfigure(0, weight=1)
        self.y += 1

        self.device_name_view = ttk.Label(box, text=t("prefix_selected_device") + ": N/A")
        self.device_name_view.grid(row=0, column=0, columnspan=3, sticky=tkinter.NSEW, padx=8, pady=8)

        self.cb_auto_connect = ttk.Checkbutton(box,
                                               text=t("toggle_device_auto_connect"),
                                               state="disabled",
                                               command=self.on_device_auto_connect_toggle,
                                               variable=self.var_auto_connect)
        self.cb_auto_connect.grid(row=1, column=0, columnspan=3, sticky=tkinter.NSEW, padx=8, pady=8)

        ttk.Label(box, text="") \
            .grid(row=2, column=0, sticky=tkinter.NSEW, padx=8)
        self.btn_connect = ttk.Button(box,
                                      state="disabled",
                                      text=t("action_connect_short"),
                                      command=self.on_device_connect)
        self.btn_connect.grid(row=2, column=1, padx=8, pady=16)
        self.btn_unpair = ttk.Button(box,
                                     state="disabled",
                                     text=t("action_unpair"),
                                     command=self.on_device_unpair)
        self.btn_unpair.grid(row=2, column=2, padx=8, pady=16)

    def on_preferred_device_select(self, _):
        addr = self.device_names[self.var_preferred_device.get()]
        self.device.set_property("config", "preferred_device", addr)

    def on_device_select(self, _):
        values = self.devices_table.item(self.devices_table.focus())["values"]
        if len(values) < 1:
            return
        addr = values[0][1:]
        name = self.device.find_property("dev_name", addr)
        is_connected = self.device.find_property("dev_connected", addr)
        is_auto_connect_enabled = self.device.find_property("dev_auto_connect", addr)

        self.device_name_view.config(text=t("prefix_selected_device") + ": " + name)
        self.var_auto_connect.set(is_auto_connect_enabled)

        btn_text_tag = "action_connect_short" if not is_connected else "action_disconnect_short"
        self.btn_connect.config(state="normal", text=t(btn_text_tag))
        self.btn_unpair.config(state="normal")
        self.cb_auto_connect.config(state="normal")

        self.selected_device_addr = addr

    def on_device_connect(self):
        val = self.device.find_property("dev_connected", self.selected_device_addr)
        self.device.set_property("dev_connected", self.selected_device_addr, not val)
        self.on_device_select(None)

    def on_device_unpair(self):
        self.device.set_property("dev_name", self.selected_device_addr, "")
        self.refresh()

    def on_device_auto_connect_toggle(self):
        val = self.var_auto_connect.get()
        self.device.set_property("dev_connected", self.selected_device_addr, val)

    def on_main_toggle(self):
        value = self.var_main_toggle.get()
        self.device.set_property("config", "dual_connect", value)


@tk_tools.ui_thread
def start(device: BaseDevice):
    ConnCenter(device).init()
