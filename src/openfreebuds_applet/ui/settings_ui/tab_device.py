import tkinter
from tkinter import ttk

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage


class DeviceSettingsTab(ttk.Frame):
    ANC_CONTROL_OPTIONS = {
        1: t("noise_control_1"),
        2: t("noise_control_2"),
        3: t("noise_control_3"),
        4: t("noise_control_4"),
    }
    DOUBLE_TAP_OPTIONS = {
        -1: t("tap_action_off"),
        1: t("tap_action_pause"),
        2: t("tap_action_next"),
        7: t("tap_action_prev"),
        0: t("tap_action_assistant")
    }

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

        device = self.manager.device
        auto_pause = device.find_property("config", "auto_pause", -1)
        self.var_auto_pause = tkinter.BooleanVar(value=(auto_pause == 1))

        long_tap_left = device.find_property("action", "long_tap_left", -99)
        self.var_long_tap_left = tkinter.BooleanVar(value=(long_tap_left == 10))

        noise_control_left = device.find_property("action", "noise_control_left", -1)
        self.var_noise_control_left = tkinter.StringVar(value=self.ANC_CONTROL_OPTIONS[noise_control_left])

        double_tap_left = device.find_property("action", "double_tap_left", -99)
        self.var_double_tap_left = tkinter.StringVar(value=self.DOUBLE_TAP_OPTIONS[double_tap_left])

        double_tap_right = device.find_property("action", "double_tap_right", -99)
        self.var_double_tap_right = tkinter.StringVar(value=self.DOUBLE_TAP_OPTIONS[double_tap_right])

        langs = device.find_property("service", "supported_languages", "").split(",")
        self.var_device_language = tkinter.StringVar(value="")

        if auto_pause != -1:
            ttk.Checkbutton(self, text=t("gesture_auto_pause"),
                            variable=self.var_auto_pause,
                            command=self._toggle_auto_pause) \
                .grid(row=20, padx=16, pady=4, sticky=tkinter.NW, columnspan=2)

        if long_tap_left != -99:
            ttk.Checkbutton(self, text=t("long_tap_global"),
                            variable=self.var_long_tap_left,
                            command=self._toggle_long_tap_left) \
                .grid(row=21, padx=16, pady=4, sticky="nws")
            c = ttk.Combobox(self, values=list(self.ANC_CONTROL_OPTIONS.values()),
                             state="readonly", textvariable=self.var_noise_control_left)
            c.bind("<<ComboboxSelected>>", self._toggle_noise_control_left)
            c.grid(row=21, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

        if double_tap_left != -99:
            ttk.Label(self, text=t("double_tap_left")) \
                .grid(row=22, padx=16, pady=4, sticky="nws")
            c = ttk.Combobox(self, values=list(self.DOUBLE_TAP_OPTIONS.values()),
                             textvariable=self.var_double_tap_left, state="readonly")
            c.bind("<<ComboboxSelected>>", self._toggle_double_tap_left)
            c.grid(row=22, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

        if double_tap_right != -99:
            ttk.Label(self, text=t("double_tap_right")) \
                .grid(row=23, padx=16, pady=4, sticky="nws")
            c = ttk.Combobox(self, values=list(self.DOUBLE_TAP_OPTIONS.values()),
                             textvariable=self.var_double_tap_right, state="readonly")
            c.bind("<<ComboboxSelected>>", self._toggle_double_tap_right)
            c.grid(row=23, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

        if len(langs) > 0:
            ttk.Label(self, text=t("submenu_device_language")) \
                .grid(row=24, padx=16, pady=4, sticky="nws")
            c = ttk.Combobox(self, values=langs, textvariable=self.var_device_language, state="readonly")
            c.bind("<<ComboboxSelected>>", self._toggle_device_language)
            c.grid(row=24, column=1, padx=16, pady=4, sticky=tkinter.NSEW)

    def _add_device_info(self):
        # Device info
        label_font = tkinter.font.Font(weight="bold")
        ttk.Label(self, text=self.settings.device_name, font=label_font) \
            .grid(row=0, padx=16, pady=16, sticky=tkinter.NW)
        ttk.Label(self, text="Bluetooth Address") \
            .grid(row=1, padx=16, pady=4, sticky=tkinter.NW)
        ttk.Label(self, text=self.settings.address) \
            .grid(row=1, padx=16, pady=4, column=1, sticky=tkinter.NW)

        row_counter = 2
        if self.manager.state == FreebudsManager.STATE_CONNECTED:
            info_props = self.device.find_group("info")
            for a in info_props:
                ttk.Label(self, text=a)\
                    .grid(row=row_counter, padx=16, pady=4, sticky=tkinter.NW)
                ttk.Label(self, text=info_props[a])\
                    .grid(row=row_counter, column=1, padx=16, pady=4, sticky=tkinter.NW)
                row_counter += 1

        # Unpair button
        # ttk.Button(self, text=t("action_change"), command=self._do_unpair)\
        #     .grid(row=row_counter, padx=16, pady=8, sticky=tkinter.NW)

    def _do_unpair(self):
        self.settings.address = ""
        self.settings.device_name = ""
        self.settings.write()

        self.manager.close(lock=False)
        self.parent.destroy()

    def _toggle_long_tap_left(self):
        enabled = self.device.find_property("action", "long_tap_left", -1) == 10
        val = -1 if enabled else 10
        self.device.set_property("action", "long_tap_left", val)

    def _toggle_noise_control_left(self, _):
        key = self.var_noise_control_left.get()
        val = _obj_reverse(self.ANC_CONTROL_OPTIONS)[key]
        self.device.set_property("action", "noise_control_left", val)

    def _toggle_auto_pause(self):
        auto_pause_value = self.device.find_property("config", "auto_pause", -1)
        self.device.set_property("config", "auto_pause", not auto_pause_value)

    def _toggle_double_tap_left(self, _):
        key = self.var_double_tap_left.get()
        val = _obj_reverse(self.DOUBLE_TAP_OPTIONS)[key]
        self.device.set_property("action", "double_tap_left", val)

    def _toggle_double_tap_right(self, _):
        key = self.var_double_tap_right.get()
        val = _obj_reverse(self.DOUBLE_TAP_OPTIONS)[key]
        self.device.set_property("action", "double_tap_right", val)

    def _toggle_device_language(self, _):
        key = self.var_device_language.get()
        self.device.set_property("service", "language", key)


def _obj_reverse(obj):
    res = {}
    for a in obj:
        res[obj[a]] = a
    return res