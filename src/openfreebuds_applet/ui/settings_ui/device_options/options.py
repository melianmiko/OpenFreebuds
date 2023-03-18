import tkinter
from tkinter import ttk

from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui.settings_ui.device_options.base import BaseDeviceOptionView


class AutoPauseOption(BaseDeviceOptionView):
    """
    Auto pause toggle checkbox option view
    """
    def is_available(self):
        auto_pause = self.device.find_property("config", "auto_pause", -1)
        return auto_pause != -1

    def build(self):
        auto_pause = self.device.find_property("config", "auto_pause", -1)
        self.variable = tkinter.BooleanVar(value=(auto_pause == 1))
        ttk.Checkbutton(self.view, text=t("gesture_auto_pause"),
                        variable=self.variable,
                        command=self.toggle) \
            .grid(row=20, padx=16, pady=4, sticky=tkinter.NW, columnspan=2)

    def toggle(self):
        auto_pause_value = self.device.find_property("config", "auto_pause", -1)
        self.device.set_property("config", "auto_pause", not auto_pause_value)


class SeparateLongTapLeft(BaseDeviceOptionView):
    """
    Separate Long tap left config option view
    """
    ANC_CONTROL_OPTIONS = {
        1: t("noise_control_1"),
        2: t("noise_control_2"),
        3: t("noise_control_3"),
        4: t("noise_control_4"),
    }

    def is_available(self):
        long_tap_left = self.device.find_property("action", "long_tap_left", -99)
        return long_tap_left != -99

    def build(self):
        long_tap_left = self.device.find_property("action", "long_tap_left", -99)
        noise_control_left = self.device.find_property("action", "noise_control_left", -1)

        self.variable = tkinter.BooleanVar(value=(long_tap_left == 10))
        self.variable2 = tkinter.StringVar(value=self.ANC_CONTROL_OPTIONS[noise_control_left])

        ttk.Checkbutton(self.view, text=t("long_tap_global"),
                        variable=self.variable,
                        command=self._toggle_long_tap_left) \
            .grid(row=21, padx=16, pady=4, sticky="nws")
        c = ttk.Combobox(self.view, values=list(self.ANC_CONTROL_OPTIONS.values()),
                         state="readonly", textvariable=self.variable2)
        c.bind("<<ComboboxSelected>>", self._toggle_noise_control_left)
        c.grid(row=21, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

    def _toggle_long_tap_left(self):
        enabled = self.device.find_property("action", "long_tap_left", -1) == 10
        val = -1 if enabled else 10
        self.device.set_property("action", "long_tap_left", val)

    def _toggle_noise_control_left(self, _):
        key = self.variable.get()
        val = utils.reverse_dict_props(self.ANC_CONTROL_OPTIONS)[key]
        self.device.set_property("action", "noise_control_left", val)


class DoubleTapOptionView(BaseDeviceOptionView):
    """
    Double tap config option view
    """
    DOUBLE_TAP_OPTIONS = {
        -1: t("tap_action_off"),
        1: t("tap_action_pause"),
        2: t("tap_action_next"),
        7: t("tap_action_prev"),
        0: t("tap_action_assistant")
    }

    def is_available(self):
        double_tap_left = self.device.find_property("action", "double_tap_left", -99)
        return double_tap_left != -99

    def build(self):
        double_tap_left = self.device.find_property("action", "double_tap_left", -99)
        double_tap_right = self.device.find_property("action", "double_tap_right", -99)
        self.variable = tkinter.StringVar(value=self.DOUBLE_TAP_OPTIONS[double_tap_left])
        self.variable2 = tkinter.StringVar(value=self.DOUBLE_TAP_OPTIONS[double_tap_right])

        ttk.Label(self.view, text=t("double_tap_left")) \
            .grid(row=22, padx=16, pady=4, sticky="nws")
        c = ttk.Combobox(self.view, values=list(self.DOUBLE_TAP_OPTIONS.values()),
                         textvariable=self.variable, state="readonly")
        c.bind("<<ComboboxSelected>>", self._toggle_double_tap_left)
        c.grid(row=22, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

        ttk.Label(self.view, text=t("double_tap_right")) \
            .grid(row=23, padx=16, pady=4, sticky="nws")
        c = ttk.Combobox(self.view, values=list(self.DOUBLE_TAP_OPTIONS.values()),
                         textvariable=self.variable2, state="readonly")
        c.bind("<<ComboboxSelected>>", self._toggle_double_tap_right)
        c.grid(row=23, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

    def _toggle_double_tap_left(self, _):
        key = self.variable.get()
        val = utils.reverse_dict_props(self.DOUBLE_TAP_OPTIONS)[key]
        self.device.set_property("action", "double_tap_left", val)

    def _toggle_double_tap_right(self, _):
        key = self.variable2.get()
        val = utils.reverse_dict_props(self.DOUBLE_TAP_OPTIONS)[key]
        self.device.set_property("action", "double_tap_right", val)


class VoiceLanguageOption(BaseDeviceOptionView):
    def is_available(self):
        langs = self.device.find_property("service", "supported_languages", "").split(",")
        return len(langs) > 0

    def build(self):
        langs = self.device.find_property("service", "supported_languages", "").split(",")
        self.variable = tkinter.StringVar(value="")

        ttk.Label(self.view, text=t("submenu_device_language")) \
            .grid(row=24, padx=16, pady=4, sticky="nws")
        c = ttk.Combobox(self.view, values=langs, textvariable=self.variable, state="readonly")
        c.bind("<<ComboboxSelected>>", self._toggle_device_language)
        c.grid(row=24, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

    def _toggle_device_language(self, _):
        key = self.variable.get()
        self.device.set_property("service", "language", key)
