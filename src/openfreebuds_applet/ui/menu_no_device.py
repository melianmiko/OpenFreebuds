import logging

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui.base import HeaderMenuPart
from openfreebuds_applet.ui.menu_app import ApplicationMenuPart
from pystrayx import Menu

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
        self.add_item(t("state_no_device"), enabled=False)
        self.include(self.footer)
