from mtrayapp import Menu

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
        for n in props:
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
        next_mode = (current + 1) % 3

        for a in range(0, 3):
            self.add_item(text=t("noise_mode_{}".format(a),),
                          action=self.set_mode, args=[a],
                          checked=current == a, default=next_mode == a)

    def set_mode(self, val):
        device = self.manager.device
        device.set_property("anc", "mode", val)
