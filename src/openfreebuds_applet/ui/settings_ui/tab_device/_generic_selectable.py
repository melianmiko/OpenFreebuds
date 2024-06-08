import tkinter
from tkinter import ttk

from openfreebuds.device.huawei.tools import reverse_dict
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui.settings_ui.tab_device._generic import DeviceSettingsSection


class SelectableDeviceOption(DeviceSettingsSection):
    prop_options = ("", "")
    prop_options_labels = {}

    prop_primary = ("", "")
    prop_primary_label = ""
    prop_secondary = ("", "")
    prop_secondary_label = ""

    def __init__(self, parent):
        super().__init__(parent)

        self.option_values = self.device.find_property(*self.prop_options).split(",")
        self.option_values = {
            v: t(v) if v not in self.prop_options_labels else t(self.prop_options_labels[v])
            for v in self.option_values
        }
        self.rev_option_values = reverse_dict(self.option_values)

        val_primary = self.device.find_property(*self.prop_primary)
        self.var_primary = tkinter.StringVar(value=self.option_values.get(val_primary, ""))
        val_secondary = self.device.find_property(*self.prop_secondary)
        if val_secondary is not None:
            self.var_secondary = tkinter.StringVar(value=self.option_values.get(val_secondary, ""))

        label = self.prop_primary[1] if self.prop_primary_label == "" else self.prop_primary_label
        ttk.Label(self, text=t(label)) \
            .grid(row=0, padx=16, pady=4, sticky="news")
        c = ttk.Combobox(self, values=list(self.option_values.values()),
                         textvariable=self.var_primary, state="readonly")
        c.bind("<<ComboboxSelected>>", self._toggle_primary)
        c.grid(row=0, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

        if val_secondary is not None:
            label = self.prop_secondary[1] if self.prop_secondary_label == "" else self.prop_secondary_label
            ttk.Label(self, text=t(label)) \
                .grid(row=1, padx=16, pady=4, sticky="news")
            c = ttk.Combobox(self, values=list(self.option_values.values()),
                             textvariable=self.var_secondary, state="readonly")
            c.bind("<<ComboboxSelected>>", self._toggle_secondary)
            c.grid(row=1, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

        self.grid_columnconfigure(0, weight=1)

    def _toggle_primary(self, _):
        v = self.rev_option_values[self.var_primary.get()]
        self.device.set_property(*self.prop_primary, v)

    def _toggle_secondary(self, _):
        v = self.rev_option_values[self.var_secondary.get()]
        self.device.set_property(*self.prop_secondary, v)
