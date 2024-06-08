import tkinter
from tkinter import ttk

from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui.settings_ui.tab_device._generic import DeviceSettingsSection


class AutoPauseSettingsSection(DeviceSettingsSection):
    required_props = {
        ("config", "auto_pause")
    }
    category_name = "Misc options"

    def __init__(self, parent):
        super().__init__(parent)

        auto_pause = self.device.find_property("config", "auto_pause", -1)
        self.variable = tkinter.BooleanVar(value=(auto_pause == 1))
        ttk.Checkbutton(self, text=t("Pause/play when you plug out headphone"),
                        variable=self.variable,
                        command=self.toggle) \
            .grid(row=0, padx=16, pady=4, sticky=tkinter.NW)

    def toggle(self):
        auto_pause_value = self.device.find_property("config", "auto_pause")
        self.device.set_property("config", "auto_pause", not auto_pause_value)
