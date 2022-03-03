from openfreebuds_applet.l18n import t, ln
from openfreebuds_applet.wrapper.tray import TrayMenu


class DeviceMenu(TrayMenu):
    """
    Device menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet
        self.power_info = DevicePowerMenu(applet)
        self.noise_control = NoiseControlMenu(applet)
        self.gestures_menu = GesturesMenu(applet)
        self.device_lang_menu = DeviceLangSetupMenu(applet)

    def on_build(self):
        compact = self.applet.settings.compact_menu
        self.include(self.power_info)
        self.add_separator()

        self.include(self.noise_control)
        self.add_separator()

        self.add_submenu(t("submenu_gestures"), self.gestures_menu, visible=compact)
        self.include(self.gestures_menu, visible=not compact)
        self.add_submenu(t("submenu_device_language"), self.device_lang_menu)


class DevicePowerMenu(TrayMenu):
    """
    Device power info menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        device = self.applet.manager.device
        for n in ["left", "right", "case"]:
            battery = device.get_property("battery_" + n, 0)
            if battery == 0:
                battery = "--"
            value = t("battery_" + n).format(battery)
            self.add_item(value, enabled=False)


class GesturesMenu(TrayMenu):
    """
    Device gestures setup menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet
        self.dt_left = DoubleTapSetupMenu(applet, "action_double_tap_left")
        self.dt_right = DoubleTapSetupMenu(applet, "action_double_tap_right")

    def on_build(self):
        device = self.applet.manager.device
        auto_pause_value = device.get_property("auto_pause", -1)
        self.add_item(t("gesture_auto_pause"),
                      action=device.set_property,
                      args=["auto_pause", not auto_pause_value],
                      checked=auto_pause_value,
                      visible=auto_pause_value != -1)

        left_2tap = device.get_property("action_double_tap_left", -99)
        self.add_submenu(t("double_tap_left"), self.dt_left,
                         visible=left_2tap != -99)

        right_2tap = device.get_property("action_double_tap_right", -99)
        self.add_submenu(t("double_tap_right"), self.dt_right,
                         visible=right_2tap != -99)


class DoubleTapSetupMenu(TrayMenu):
    """
    Noise control menu
    """
    VARIANTS = {
        "tap_action_off": -1,
        "tap_action_pause": 1,
        "tap_action_next": 2,
        "tap_action_prev": 7,
        "tap_action_assistant": 0
    }

    def __init__(self, applet, prop):
        super().__init__()
        self.applet = applet
        self.prop = prop

    def on_build(self):
        device = self.applet.manager.device
        current = device.get_property(self.prop, -99)
        for name in self.VARIANTS:
            value = self.VARIANTS[name]
            self.add_item(t(name), self.set_value, checked=current == value, args=[value])

    def set_value(self, value):
        device = self.applet.manager.device
        device.set_property(self.prop, value)


class NoiseControlMenu(TrayMenu):
    """
    Noise control menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        device = self.applet.manager.device
        current = device.get_property("noise_mode", -1)
        next_mode = (current + 1) % 3

        for a in range(0, 3):
            self.add_item(text=t("noise_mode_{}".format(a),),
                          action=self.set_mode, args=[a],
                          checked=current == a, default=next_mode == a)

    def set_mode(self, val):
        device = self.applet.manager.device
        device.set_property("noise_mode", val)


class DeviceLangSetupMenu(TrayMenu):
    """
    Noise control menu
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        device = self.applet.manager.device
        langs = device.get_property("supported_languages", "").split(",")
        if len(langs) == 0:
            return

        for lang in langs:
            self.add_item(ln(lang),
                          action=device.set_property,
                          args=["language", lang])
