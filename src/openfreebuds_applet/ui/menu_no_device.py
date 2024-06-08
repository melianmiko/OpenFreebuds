from openfreebuds.logger import create_log
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui.base import HeaderMenuPart
from openfreebuds_applet.ui.i18n_mappings import MANAGER_STATE_NAMES
from openfreebuds_applet.ui.menu_app import ApplicationMenuPart
from pystrayx import Menu

log = create_log("NoDeviceUI")


class DeviceOfflineMenu(Menu):
    def __init__(self, applet):
        super().__init__()
        self.manager = applet.manager  # type: FreebudsManager
        self.footer = ApplicationMenuPart(applet)
        self.header = HeaderMenuPart(applet)

    def on_build(self):
        state_title = MANAGER_STATE_NAMES[self.manager.state]

        self.include(self.header)
        self.add_item(t(state_title), enabled=False)
        self.include(self.footer)


class DeviceScanMenu(Menu):
    def __init__(self, applet):
        super().__init__()
        self.manager = applet.manager  # type: FreebudsManager
        self.settings = applet.settings  # type: SettingsStorage
        self.footer = ApplicationMenuPart(applet)

    def on_build(self):
        self.add_item(t("Device not selected"), enabled=False)
        self.include(self.footer)
