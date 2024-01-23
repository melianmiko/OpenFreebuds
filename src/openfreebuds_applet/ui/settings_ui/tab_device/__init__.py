import logging
from tkinter import ttk

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage

import tkinter
import tkinter.font

from openfreebuds_applet.ui.settings_ui.tab_device.config_equalizer import EqualizerSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.config_sound_quality import SoundQualitySettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.device_info import DeviceInfoSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.dual_connect_devices import DualConnectDevicesSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_double import DoubleTapSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_double_in_call import DoubleTapInCallSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_long import LongTapSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_long_in_call import LongTapInCallSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_long_separate import LongTapSeparateSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_long_separate_nc import NoiseControlSeparateSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_power import PowerButtonSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.gesture_swipe import SwipeGestureSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.voice_language import LanguageSettingsSection
from openfreebuds_applet.ui.settings_ui.tab_device.tws_auto_pause import AutoPauseSettingsSection


class DeviceSettingsTab(ttk.Frame):
    def __init__(
            self,
            parent: tkinter.Toplevel,
            manager: FreebudsManager,
            settings: SettingsStorage,
            allowed_categories=None,
            with_header=True
    ):
        super().__init__(parent)
        device = manager.device

        self.manager = manager
        self.device = device
        self.settings = settings
        self.allowed_categories = allowed_categories
        self.parent = parent
        self.is_recording = False
        self.grid_columnconfigure(0, weight=1)

        if with_header:
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
            DualConnectDevicesSettingsSection,
            DoubleTapSettingsSection,
            DoubleTapInCallSettingsSection,
            LongTapSettingsSection,
            LongTapSeparateSettingsSection,
            LongTapInCallSettingsSection,
            NoiseControlSeparateSettingsSection,
            SwipeGestureSettingsSection,
            PowerButtonSettingsSection,
            SoundQualitySettingsSection,
            EqualizerSettingsSection,
            AutoPauseSettingsSection,
            LanguageSettingsSection,
        ]

        self.button_row = tkinter.Frame(self)
        self.button_row.grid(row=20, columnspan=2, sticky=tkinter.NSEW, pady=4, padx=8)
        self.button_row_x = 0

        y = 30
        for Option in option_views:
            category = Option.category_name
            if Option.should_be_visible(self.manager, Option.required_props):
                if self.allowed_categories is not None and category not in self.allowed_categories:
                    continue
                if category not in self.categories:
                    ttk.Label(self, text=t(category), font=label_fnt)\
                        .grid(row=y, column=0, columnspan=2, sticky=tkinter.NW, padx=16, pady=16)
                    self.categories[category] = y + 1
                    y += 20
                view = Option((self, self.manager.device))
                if view.action_button is not None:
                    self.add_action_button(view)
                view.grid(row=self.categories[category], columnspan=2, sticky=tkinter.NSEW)
                self.categories[category] += 1

    def add_action_button(self, view):
        ttk.Button(self.button_row,
                   text=view.action_button,
                   command=lambda *args: view.on_action_button_click())\
            .grid(row=0, column=self.button_row_x, padx=8)
        self.button_row_x += 1

    def _add_device_info(self):
        # Device info
        label_font = tkinter.font.Font(weight="bold")
        ttk.Label(self, text=self.settings.device_name, font=label_font) \
            .grid(row=0, padx=16, pady=16, sticky=tkinter.NW)
        ttk.Label(self, text=t("device_info_address")) \
            .grid(row=1, padx=16, pady=4, sticky=tkinter.NW)
        ttk.Label(self, text=self.settings.address) \
            .grid(row=1, padx=16, pady=4, column=1, sticky=tkinter.NW)
