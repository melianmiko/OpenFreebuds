import logging

import openfreebuds_backend
from openfreebuds import event_bus, device_names
from openfreebuds.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.wrapper.tray import TrayMenu
from openfreebuds_backend import bt_list_devices

log = logging.getLogger("NoDeviceUI")


class DeviceOfflineMenu(TrayMenu):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager          # type: FreebudsManager

    def on_build(self):
        self.add_item(t("mgr_state_{}".format(self.manager.state)),
                      enabled=False)


class DeviceScanMenu(TrayMenu):
    def __init__(self, manager, settings):
        super().__init__()
        self.manager = manager          # type: FreebudsManager
        self.settings = settings        # type: SettingsStorage

    def on_build(self):
        devices = bt_list_devices()

        self.add_item(t("select_device"), enabled=False)

        for data in devices:
            self.add_item(data["name"], self.on_device, args=[data])

        self.add_separator()
        self.add_item(t("action_refresh_list"), self.refresh)

    @staticmethod
    def refresh():
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def on_device(self, data):
        name = data["name"]
        if not device_names.is_supported(name):
            openfreebuds_backend.ask_question(t("question_not_supported"),
                                              lambda r: self.do_device(data, r))
            return

        self.do_device(data, True)

    def do_device(self, data, ui_result):
        name = data["name"]
        address = data["address"]

        if not ui_result:
            return

        self.manager.set_device(address)
        self.settings.device_name = name
        self.settings.address = address
        self.settings.write()
