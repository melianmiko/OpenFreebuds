import logging

from openfreebuds.logger import create_log
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import GenericModule
from openfreebuds_applet.modules.update_check._update_tool import FreebudsUpdater

log = create_log("UpdateChecker")


class Module(GenericModule):
    ident = "update_check"
    name = t("module_updater")
    description = t("updater_info")
    order = 2
    def_settings = {
        "enabled": True
    }

    def __init__(self):
        super().__init__()
        self.updater: FreebudsUpdater | None = None

    def _mainloop(self):
        self.updater = FreebudsUpdater(self.app_settings)
        self.updater.ignore_ppa = True
        self.updater.start()

    def get_result(self):
        if not self.updater:
            return False, ""
        return self.updater.has_update, self.updater.new_version

    def show_update_message(self):
        if not self.updater:
            return
        self.updater.show_update_dialog()
