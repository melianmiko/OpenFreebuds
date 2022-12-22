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

        self.enable_hotkeys = False
        self.enable_server = False
        self.server_access = False
        self.enable_update_dialog = True
        self.enable_debug_features = False
        self.enable_sleep = False

        self.hotkeys_config_2 = {
            "next_mode": "<ctrl>+<alt>+q"
        }

        self._read()

    def _read(self):
        path = utils.get_settings_path()
        logging.debug("Using config path: " + path)
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
        path = utils.get_settings_path()

        with open(path, "w") as f:
            f.write(json.dumps(self.__dict__))

        logging.debug("config file updated")
