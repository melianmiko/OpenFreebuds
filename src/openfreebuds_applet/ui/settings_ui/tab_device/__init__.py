import logging
from tkinter import ttk

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage

import tkinter
import tkinter.font

from openfreebuds_applet.ui.settings_ui.tab_device.device_info import DeviceInfoSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_double import DoubleTapSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_double_in_call import DoubleTapInCallSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_long import LongTapSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_long_separate import LongTapSeparateSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_long_separate_nc import NoiseControlSeparateSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_power import PowerButtonSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.voice_language import LanguageSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.tws_auto_pause import AutoPauseSettingsSection


class DeviceSettingsTab(ttk.Frame):
    def __init__(self, parent: tkinter.Toplevel, manager: FreebudsManager, settings: SettingsStorage):
        super().__init__(parent)
        device = manager.device

        self.manager = manager
        self.device = device
        self.settings = settings
        self.parent = parent
        self.is_recording = False
        self.grid_columnconfigure(0, weight=1)

        self._add_device_info()
        self._add_device_settings()

    def _add_device_settings(self):
        if self.manager.state != FreebudsManager.STATE_CONNECTED:
            return

        self.categories = {
            "main": 10
        }
        label_fnt = tkinter.font.Font(weight="bold")

        option_views = [
            DeviceInfoSettingsSection,
            DoubleTapSettingsSection,
            DoubleTapInCallSettingsSection,
            LongTapSettingsSection,
            LongTapSeparateSettingsSection,
            NoiseControlSeparateSettingsSection,
            PowerButtonSettingsSection,
            AutoPauseSettingsSection,
            LanguageSettingsSection,
        ]

        y = 20
        for Option in option_views:
            category = Option.category_name
            if Option.should_be_visible(self.manager, Option.required_props):
                if category not in self.categories:
                    ttk.Label(self, text=t(category), font=label_fnt)\
                        .grid(row=y, column=0, columnspan=2, sticky=tkinter.NW, padx=16, pady=16)
                    self.categories[category] = y + 1
                    y += 20
                Option((self, self.manager.device))\
                    .grid(row=self.categories[category], columnspan=2, sticky=tkinter.NSEW)
                self.categories[category] += 1

    def _add_device_info(self):
        # Device info
        label_font = tkinter.font.Font(weight="bold")
        ttk.Label(self, text=self.settings.device_name, font=label_font) \
            .grid(row=0, padx=16, pady=16, sticky=tkinter.NW)
        ttk.Label(self, text=t("device_info_address")) \
            .grid(row=1, padx=16, pady=4, sticky=tkinter.NW)
        ttk.Label(self, text=self.settings.address) \
            .grid(row=1, padx=16, pady=4, column=1, sticky=tkinter.NW)
