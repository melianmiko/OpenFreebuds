import logging

from mtrayapp import Menu

from openfreebuds import event_bus, device
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import profile_select_ui
from openfreebuds_applet.ui.base import HeaderMenuPart
from openfreebuds_applet.ui.menu_app import ApplicationMenuPart
from openfreebuds_backend import bt_list_devices

log = logging.getLogger("NoDeviceUI")


class DeviceOfflineMenu(Menu):
    def __init__(self, applet):
        super().__init__()
        self.manager = applet.manager  # type: FreebudsManager
        self.footer = ApplicationMenuPart(applet)
        self.header = HeaderMenuPart(applet)

    def on_build(self):
        self.include(self.header)
        self.add_item(t("mgr_state_{}".format(self.manager.state)),
                      enabled=False)
        self.include(self.footer)


class DeviceScanMenu(Menu):
    def __init__(self, applet):
        super().__init__()
        self.manager = applet.manager  # type: FreebudsManager
        self.settings = applet.settings  # type: SettingsStorage
        self.footer = ApplicationMenuPart(applet)

    def on_build(self):
        devices = bt_list_devices()
        self.add_item(t("select_device"), enabled=False)

        for data in devices:
            self.add_item(data["name"], self.on_device, args=[data])

        self.add_separator()
        self.add_item(t("action_refresh_list"), self.refresh)

        self.include(self.footer)

    @staticmethod
    def refresh():
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def on_device(self, data):
        name = data["name"]
        address = data["address"]

        if not device.is_supported(name):
            profile_select_ui.start(address, self.settings, self.manager)
            return

        self.settings.device_name = name
        self.settings.address = address
        self.settings.is_device_mocked = False
        self.settings.write()

        self.manager.set_device(name, address)

