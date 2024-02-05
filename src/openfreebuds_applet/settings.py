import json
import logging
import os

from openfreebuds_applet import utils


class SettingsStorage:
    def __init__(self):
        self.address = ""
        self.device_name = ""
        self.is_device_mocked = False
        self.device_autoconfig = True

        self.language = ""
        self.theme = "auto"
        self.icon_theme = "auto"
        self.first_run = True
        self.modules = {}
        self.context_menu_extras = ["equalizer", "dual_connect"]

        self._read()

    def _read(self):
        path = utils.get_app_storage_dir() / "settings.json"
        logging.debug(f"Using config path: {path}")
        if not os.path.isfile(path):
            return

        try:
            with open(path, "r") as f:
                data = json.loads(f.read())
                for a in data:
                    setattr(self, a, data[a])
        except json.JSONDecodeError:
            logging.warning("Can't load saved config")

    def write(self):
        path = utils.get_app_storage_dir() / "settings.json"

        with open(path, "w") as f:
            f.write(json.dumps(self.__dict__))

        logging.debug("config file updated")
