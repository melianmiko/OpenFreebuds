import logging
import tkinter

from mmk_updater import UpdaterTool
from mmk_updater.ui_tkinter import TkinterUiMod
from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import utils
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools

release_url = "https://st.melianmiko.ru/openfreebuds/release.json"
log = logging.getLogger("UpdateChecker")


class Data:
    updater = None      # type: FreebudsUpdater


def get_result():
    return Data.updater.has_update, Data.updater.new_version


def start(applet):
    Data.updater = FreebudsUpdater(applet.settings)
    Data.updater.start()


def show_update_message():
    Data.updater.show_update_dialog()


class FreebudsUpdateUiMod(TkinterUiMod):
    def __init__(self):
        super().__init__()

    def mk_window(self) -> tkinter.Tk:
        return tk_tools.create_themed()


class FreebudsUpdater(UpdaterTool):
    def __init__(self, settings: SettingsStorage):
        super().__init__(release_url, utils.get_version()[0], FreebudsUpdateUiMod())
        log.debug(self.current_version)
        self.new_version = ""
        self.has_update = False
        self.settings = settings

    def should_show_update_ui(self):
        if not self.settings.enable_update_dialog:
            return False
        return super().should_show_update_ui()

    def on_release_data(self):
        self.new_version = self.release_data["version"]
        self.has_update = self.current_version != self.release_data["version"]
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)
