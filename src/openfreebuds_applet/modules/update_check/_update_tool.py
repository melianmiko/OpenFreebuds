import logging

from mmk_updater import UpdaterTool

from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds.logger import create_log
from openfreebuds_applet import utils
from openfreebuds_applet.modules.update_check._update_ui import FreebudsUpdateUiMod
from openfreebuds_applet.modules.update_check._url import release_url
from openfreebuds_applet.settings import SettingsStorage

log = create_log("UpdateChecker")


class FreebudsUpdater(UpdaterTool):
    def __init__(self, settings: SettingsStorage):
        super().__init__(release_url, utils.get_version(), FreebudsUpdateUiMod())
        log.debug(self.current_version)
        self.new_version = ""
        self.has_update = False
        self.settings = settings

    def should_show_update_ui(self):
        return super().should_show_update_ui()

    def on_release_data(self):
        self.new_version = self.release_data["version"]
        self.has_update = self.current_version != self.release_data["version"]
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def start(self):
        self._process()
