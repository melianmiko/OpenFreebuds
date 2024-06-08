import tkinter
from tkinter import ttk

from openfreebuds_applet.dialog import device_info_dialog
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui.settings_ui.tab_device._generic import DeviceSettingsSection


class DeviceInfoSettingsSection(DeviceSettingsSection):
    action_button = t("Info...")
    required_props = [
        ("info", "software_ver"),
    ]

    def __init__(self, params):
        super().__init__(params)
        ttk.Label(self, text=t("Firmware version")) \
            .grid(row=1, padx=16, pady=4, sticky=tkinter.NW)
        ttk.Label(self, text=self.device.find_property("info", "software_ver")) \
            .grid(row=1, padx=16, pady=4, column=1, sticky=tkinter.NW)

        self.grid_columnconfigure(0, weight=1)

    def on_action_button_click(self):
        device_info_dialog.start(self.device)
