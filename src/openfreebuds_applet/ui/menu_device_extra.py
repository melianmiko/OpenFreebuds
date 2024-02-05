from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from pystrayx import Menu


class EqualizerPresetMenu(Menu):
    def __init__(self, manager: FreebudsManager):
        super().__init__()
        self.manager = manager

    def on_build(self):
        device = self.manager.device
        current = device.find_property("config", "equalizer_preset", -99)
        if current == -99:
            return
        options = device.find_property("config", "equalizer_preset_options").split(",")

        for val in options:
            self.add_item(text=t(val),
                          action=self.set_value,
                          args=[val],
                          checked=current == val)

    def set_value(self, val):
        self.manager.device.set_property("config", "equalizer_preset", val)


class DualConnectMenu(Menu):
    def __init__(self, manager: FreebudsManager):
        super().__init__()
        self.manager = manager

    def on_build(self):
        device = self.manager.device
        if device.find_property("config", "dual_connect", None) is None:
            return

        for addr, name in device.find_group("dev_name").items():
            is_connected = device.find_property("dev_connected", addr, False)
            self.add_item(text=name,
                          action=self.toggle,
                          args=[addr],
                          checked=is_connected)

    def toggle(self, addr):
        is_connected = self.manager.device.find_property("dev_connected", addr, False)
        self.manager.device.set_property("dev_connected", addr, not is_connected)
