import json
import logging
import os
import platform


def _get_file_path():
    if platform.system() == "Windows":
        appdata = os.getenv("APPDATA")
        return appdata + "\\openfreebuds.json"
    else:
        home = os.getenv("HOME")
        return home + "/.config/openfreebuds.json"


class SettingsStorage:
    def __init__(self):
        self.address = ""
        self.device_name = ""
        self.theme = "auto"

        self._read()

    def _read(self):
        path = _get_file_path()
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
        path = _get_file_path()

        with open(path, "w") as f:
            f.write(json.dumps(self.__dict__))

        logging.debug("config file updated")
