from pystrayx import Menu

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui.base import HeaderMenuPart
from openfreebuds_applet.ui.menu_app import ApplicationMenuPart


class DeviceMenu(Menu):
    """
    Device menu
    """

    def __init__(self, applet):
        super().__init__()
        self.manager = applet.manager          # type: FreebudsManager
        self.settings = applet.settings        # type: SettingsStorage
        self.footer = ApplicationMenuPart(applet)
        self.header = HeaderMenuPart(applet)

        self.power_info = DevicePowerMenu(self.manager, self.settings)
        self.noise_control = NoiseControlMenu(self.manager)

    def on_build(self):
        self.include(self.header)
        self.include(self.power_info)
        self.add_separator()

        self.include(self.noise_control)
        self.add_separator()

        self.include(self.footer)


class DevicePowerMenu(Menu):
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
        if "case" in props:
            # TWS view
            self._build_tws(props)
            return

        if "global" in props:
            # Global only view
            value = "--" if props["global"] == 0 else props["global"]
            self.add_item(t("battery_global").format(value), enabled=False)

    def _build_tws(self, props):
        for n in ["left", "right", "case"]:
            battery = props[n]
            if battery == 0:
                battery = "--"
            value = t("battery_" + n).format(battery)
            self.add_item(value, enabled=False)


class NoiseControlMenu(Menu):
    """
    Noise control menu
    """

    def __init__(self, manager: FreebudsManager):
        super().__init__()
        self.manager = manager

    def on_build(self):
        device = self.manager.device
        current = device.find_property("anc", "mode", -1)
        if current == -1:
            return
        options = list(device.find_property("anc", "mode_options").split(","))
        next_mode = options[(options.index(current) + 1) % len(options)]

        for a in options:
            self.add_item(text=t("noise_mode_{}".format(a)),
                          action=self.set_mode,
                          args=[a],
                          checked=current == a,
                          default=next_mode == a)

        if device.find_property("anc", "level_options", ""):
            self.add_submenu(t("anc_level"), AncLevelSubmenu(self.manager))

    def set_mode(self, val):
        self.manager.device.set_property("anc", "mode", val)


class AncLevelSubmenu(Menu):
    def __init__(self, manager: FreebudsManager):
        super().__init__()
        self.manager = manager

    def on_build(self):
        device = self.manager.device
        current = device.find_property("anc", "level", -1)
        if current == -1:
            return
        options = device.find_property("anc", "level_options").split(",")

        for val in options:
            self.add_item(text=t(f"anc_level_{val}"),
                          action=self.set_level,
                          args=[val],
                          checked=current == val)

    def set_level(self, val):
        self.manager.device.set_property("anc", "level", val)
