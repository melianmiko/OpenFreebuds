import glob
import json
import logging
import urllib.request
import webbrowser

import openfreebuds_backend
import mmk_updater
from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t

release_url = "https://st.melianmiko.ru/openfreebuds/release.json"
log = logging.getLogger("UpdateChecker")


class Data:
    show_messages = True
    has_update = False
    new_version = ""
    tool = None     # type: mmk_updater.UpdaterTool


def get_result():
    return Data.has_update, Data.new_version


def start(applet):
    Data.show_messages = applet.settings.enable_update_dialog
    Data.tool = UpdaterTool()
    Data.tool.start()


def show_update_message():
    Data.tool.show_update_dialog()


class UpdaterTool(mmk_updater.UpdaterTool):
    def __init__(self):
        super(UpdaterTool, self).__init__(release_url, utils.get_version()[0])
        log.debug(self.current_version)

    def should_show_update_ui(self):
        if not Data.show_messages:
            return False
        return super().should_show_update_ui()

    def on_release_data(self):
        Data.new_version = self.release_data["version"]
        Data.has_update = self.current_version != self.release_data["version"]
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


