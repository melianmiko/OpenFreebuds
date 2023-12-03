import tkinter
from tkinter import ttk

from openfreebuds.device import BaseDevice
from openfreebuds.manager import FreebudsManager


class DeviceSettingsSection(tkinter.Frame):
    required_props = []
    category_name = "main"

    def __init__(self, params):
        super().__init__(params[0])
        self.device: BaseDevice = params[1]

    @staticmethod
    def should_be_visible(manager: FreebudsManager, required_props):
        for group, prop in required_props:
            if manager.device.find_property(group, prop) is None:
                return False
        return True
