import json

import openfreebuds_backend
from openfreebuds_qt.constants import STORAGE_PATH

CONFIG_PATH = STORAGE_PATH / "openfreebuds_qt.json"


class OfbQtConfigParser:
    instance = None

    def __init__(self):
        self.data = {}
        if CONFIG_PATH.is_file():
            with open(CONFIG_PATH, "r") as f:
                self.data = json.loads(f.read())

    @staticmethod
    def get_instance():
        if OfbQtConfigParser.instance is None:
            OfbQtConfigParser.instance = OfbQtConfigParser()
        return OfbQtConfigParser.instance

    def get(self, section: str, key: str, fallback: any = None):
        try:
            return self.data[section][key]
        except KeyError:
            return fallback

    def set(self, section: str, key: str, value: any):
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value

    def save(self):
        with open(CONFIG_PATH, "w") as f:
            f.write(json.dumps(self.data, ensure_ascii=False, indent=4))

    def set_device_data(self, name: str, address: str):
        self.set("device", "name", name)
        self.set("device", "address", address)

    def get_tray_icon_theme(self):
        value = self.get("ui", "tray_icon_theme", "auto")
        if value != "auto":
            return value
        return "dark" if openfreebuds_backend.is_dark_theme() else "light"
