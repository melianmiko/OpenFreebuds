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
    prop_primary_label = "Device language:"
    category_name = "Misc options"

    required_props = [
        ("service", "supported_languages"),
    ]
