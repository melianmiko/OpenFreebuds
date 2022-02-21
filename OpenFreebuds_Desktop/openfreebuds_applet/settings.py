import json
import logging
import os

from openfreebuds_applet import tools


class SettingsStorage:
    def __init__(self):
        self.address = ""
        self.device_name = ""
        self.theme = "auto"

        self.enable_hotkeys = False
        self.hotkey_next_mode = "<ctrl>+<alt>+q"

        self.enable_flask = False

        self._read()

    def _read(self):
        path = tools.get_settings_path()
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
        path = tools.get_settings_path()

        with open(path, "w") as f:
            f.write(json.dumps(self.__dict__))

        logging.debug("config file updated")
