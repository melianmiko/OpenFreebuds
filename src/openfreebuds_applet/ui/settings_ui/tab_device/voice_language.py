import tkinter
from tkinter import ttk

from openfreebuds.device.huawei.tools import reverse_dict
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui.settings_ui.tab_device._generic import DeviceSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class LanguageSettingsSection(SelectableDeviceOption):
    prop_options = ("service", "supported_languages")
    prop_primary = ("service", "language")
    prop_primary_label = "submenu_device_language"
    category_name = "setup_category_config"

    required_props = [
        ("service", "supported_languages"),
    ]
    #
    # def __init__(self, parent):
    #     super().__init__(parent)
    #
    #     self.option_values = self.device.find_property("service", "supported_languages").split(",")
    #
    #     self.var = tkinter.StringVar(value="")
    #
    #     ttk.Label(self, text=t("submenu_device_language")) \
    #         .grid(row=0, padx=16, pady=4, sticky="news")
    #     c = ttk.Combobox(self, values=list(self.option_values), textvariable=self.var, state="readonly")
    #     c.bind("<<ComboboxSelected>>", self._toggle_device_language)
    #     c.grid(row=0, column=1, padx=16, pady=4, sticky=tkinter.NSEW)
    #
    #     self.grid_columnconfigure(0, weight=1)
    #
    # def _toggle_device_language(self, _):
    #     self.device.set_property("service", "language", self.var.get())
