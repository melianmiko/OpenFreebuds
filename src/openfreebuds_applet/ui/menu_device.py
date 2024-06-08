from openfreebuds_applet.ui.i18n_mappings import ANC_MODE_MAPPINGS, ANC_LEVEL_MAPPINGS
from openfreebuds_applet.ui.menu_device_extra import EqualizerPresetMenu, DualConnectMenu
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

        if "equalizer" in self.settings.context_menu_extras:
            self.add_submenu(t("Equalizer"), EqualizerPresetMenu(self.manager))
        if "dual_connect" in self.settings.context_menu_extras:
            self.add_submenu(t("Dual-connection"), DualConnectMenu(self.manager))
        if len(self.settings.context_menu_extras) > 0:
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
            title = t("Battery:")
            value = "--" if props["global"] == 0 else props["global"]
            self.add_item(f"{title} {value}%", enabled=False)

    def _build_tws(self, props):
        items = [
            # [key, title]
            ["left", t("Left headphone:")],
            ["right", t("Right headphone:")],
            ["case", t("Battery case:")],
        ]

        for key, title in items:
            battery = props[key]
            if battery == 0:
                battery = "--"
            value = f"{title} {battery}%"
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
            self.add_item(text=t(ANC_MODE_MAPPINGS.get(a)),
                          action=self.set_mode,
                          args=[a],
                          checked=current == a,
                          default=next_mode == a)

        if device.find_property("anc", "level_options", ""):
            self.add_submenu(t("Intensity..."), AncLevelSubmenu(self.manager))

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
            self.add_item(text=t(ANC_LEVEL_MAPPINGS.get(val)),
                          action=self.set_level,
                          args=[val],
                          checked=current == val)

    def set_level(self, val):
        self.manager.device.set_property("anc", "level", val)
