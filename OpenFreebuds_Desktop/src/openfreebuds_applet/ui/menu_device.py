from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t, ln
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.wrapper.tray import TrayMenu


class DeviceMenu(TrayMenu):
    """
    Device menu
    """

    def __init__(self, manager:  FreebudsManager, settings: SettingsStorage):
        super().__init__()
        self.manager = manager
        self.settings = settings
        self.power_info = DevicePowerMenu(manager, settings)
        self.noise_control = NoiseControlMenu(manager)
        self.gestures_menu = GesturesMenu(manager, settings)
        self.device_lang_menu = DeviceLangSetupMenu(manager)

    def on_build(self):
        compact = self.settings.compact_menu
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

    def __init__(self, manager:  FreebudsManager, settings: SettingsStorage):
        super().__init__()
        self.manager = manager
        self.settings = settings

    def on_build(self):
        device = self.manager.device
        props = device.find_group("battery")
        for n in props:
            battery = props[n]
            if battery == 0:
                battery = "--"
            value = t("battery_" + n).format(battery)
            self.add_item(value, enabled=False)


class GesturesMenu(TrayMenu):
    """
    Device gestures setup menu
    """

    def __init__(self, manager:  FreebudsManager, settings: SettingsStorage):
        super().__init__()
        self.manager = manager
        self.settings = settings

        self.lt_glob = ANCControlSetupMenu(manager)
        self.dt_left = DoubleTapSetupMenu(manager, "double_tap_left")
        self.dt_right = DoubleTapSetupMenu(manager, "double_tap_right")

    def on_build(self):
        device = self.manager.device

        auto_pause_value = device.find_property("config", "auto_pause", -1)
        self.add_item(t("gesture_auto_pause"),
                      action=device.set_property,
                      args=["config", "auto_pause", not auto_pause_value],
                      checked=auto_pause_value,
                      visible=auto_pause_value != -1)

        left_long = device.find_property("action", "long_tap_left", -1) == 10
        self.add_submenu(t("long_tap_global"), self.lt_glob,
                         visible=left_long != -99)

        left_2tap = device.find_property("action", "double_tap_left", -99)
        self.add_submenu(t("double_tap_left"), self.dt_left,
                         visible=left_2tap != -99)

        right_2tap = device.find_property("action", "double_tap_right", -99)
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

    def __init__(self, manager: FreebudsManager, prop: str):
        super().__init__()
        self.manager = manager
        self.prop = prop

    def on_build(self):
        device = self.manager.device
        current = device.find_property("action", self.prop, -99)
        for name in self.VARIANTS:
            value = self.VARIANTS[name]
            self.add_item(t(name),
                          action=device.set_property,
                          checked=current == value,
                          args=["action", self.prop, value])


class ANCControlSetupMenu(TrayMenu):
    VARIANTS = {
        2: "noise_control_2",
        1: "noise_control_1",
        4: "noise_control_4",
        3: "noise_control_3"
    }

    def __init__(self, manager: FreebudsManager):
        super().__init__()
        self.manager = manager

    def on_build(self):
        device = self.manager.device
        enabled = device.find_property("action", "long_tap_left", -1) == 10
        current = device.find_property("action", "noise_control_left", -1)

        self.add_item(t("prop_enabled"), action=self.on_global_toggle, checked=enabled)
        self.add_separator()
        for value in self.VARIANTS:
            str_key = self.VARIANTS[value]
            self.add_item(t(str_key), action=self.set_current, checked=current == value, args=[value])

    def on_global_toggle(self):
        device = self.manager.device
        enabled = device.find_property("action", "long_tap_left", -1) == 10
        val = -1 if enabled else 10

        device.set_property("action", "long_tap_left", val)

    def set_current(self, value):
        device = self.manager.device
        device.set_property("action", "noise_control_left", value)


class NoiseControlMenu(TrayMenu):
    """
    Noise control menu
    """

    def __init__(self, manager: FreebudsManager):
        super().__init__()
        self.manager = manager

    def on_build(self):
        device = self.manager.device
        current = device.find_property("anc", "mode", -1)
        next_mode = (current + 1) % 3

        for a in range(0, 3):
            self.add_item(text=t("noise_mode_{}".format(a),),
                          action=self.set_mode, args=[a],
                          checked=current == a, default=next_mode == a)

    def set_mode(self, val):
        device = self.manager.device
        device.set_property("anc", "mode", val)


class DeviceLangSetupMenu(TrayMenu):
    """
    Noise control menu
    """

    def __init__(self, manager: FreebudsManager):
        super().__init__()
        self.manager = manager

    def on_build(self):
        device = self.manager.device
        langs = device.find_property("service", "supported_languages").split(",")
        if len(langs) == 0:
            return

        for lang in langs:
            self.add_item(ln(lang),
                          action=device.set_property,
                          args=["service", "language", lang])
