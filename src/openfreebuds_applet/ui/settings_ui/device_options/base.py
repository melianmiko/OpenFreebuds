from openfreebuds.device.generic.base import BaseDevice


class BaseDeviceOptionView:
    def __init__(self):
        self.device: BaseDevice | None = None
        self.view = None
        self.variable = None
        self.variable2 = None

    def init(self, view, device):
        self.view = view
        self.device = device
        self.on_ready()

    def on_ready(self):
        pass

    # noinspection PyMethodMayBeStatic
    def is_available(self):
        return False

    def build(self):
        pass
