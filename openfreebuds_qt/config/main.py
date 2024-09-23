import json
import os.path
from functools import cached_property
from typing import Optional

from qasync import QApplication

from openfreebuds.constants import STORAGE_PATH
from openfreebuds_backend import is_dark_taskbar

CONFIG_PATH = STORAGE_PATH / "openfreebuds_qt.json"


class OfbQtConfigParser:
    instance = None

    def __init__(self):
        self.data = {}
        self.qt_is_dark_theme: bool = False
        if CONFIG_PATH.is_file():
            with open(CONFIG_PATH, "r") as f:
                self.data = json.loads(f.read())

    @staticmethod
    def get_instance():
        if OfbQtConfigParser.instance is None:
            OfbQtConfigParser.instance = OfbQtConfigParser()
        return OfbQtConfigParser.instance

    def get(self, section: str, key: Optional[str] = None, fallback: any = None):
        try:
            if key is None:
                return self.data[section]
            return self.data[section][key]
        except KeyError:
            return fallback

    def set(self, section: str, key: str, value: any):
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value

    def remove(self, section: str, key: str):
        if section not in self.data or key not in self.data[section]:
            return
        del self.data[section][key]

    def save(self):
        with open(CONFIG_PATH, "w") as f:
            f.write(json.dumps(self.data, ensure_ascii=False, indent=4))

    def set_device_data(self, name: str, address: str):
        self.set("device", "name", name)
        self.set("device", "address", address)

    def update_fallback_values(self, ctx: QApplication):
        palette = ctx.palette()
        self.qt_is_dark_theme = palette.text().color().value() > palette.base().color().value()

    def get_tray_icon_theme(self):
        value = self.get("ui", "tray_icon_theme", "auto")
        if value != "auto":
            return value

        # Auto-detect using ofb-backend
        backend_theme = is_dark_taskbar()
        if backend_theme is not None:
            return "dark" if not backend_theme else "light"

        # Auto-detect using qt
        return self.qt_is_dark_theme

    @cached_property
    def is_containerized_app(self):
        return os.path.isfile("/app/is_container")
