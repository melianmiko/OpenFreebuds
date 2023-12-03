import importlib
import logging
from pkgutil import walk_packages

from openfreebuds.logger import create_log
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.modules.generic import GenericModule, FailedModule
from openfreebuds_applet.settings import SettingsStorage

log = create_log("ModuleManager")


class ModuleManager:
    def __init__(self, settings: SettingsStorage, manager: FreebudsManager):
        self.modules: dict[str, GenericModule] = {}
        self._app_settings = settings
        self._app_manager = manager
        self._load()

    def get(self, name: str):
        if name not in self.modules:
            return None
        return self.modules[name]

    def _load(self):
        for o in walk_packages(__path__):
            if o.ispkg:
                try:
                    imported = importlib.import_module(f"openfreebuds_applet.modules.{o.name}")
                    module = imported.Module()  # type: GenericModule
                    module.connect(self._app_settings, self._app_manager)
                except ModuleNotFoundError as e:
                    module = FailedModule(o.name, str(e))
                self.modules[module.ident] = module

    def autostart(self):
        for ident in self.modules:
            if self.modules[ident].get_property("enabled"):
                self.modules[ident].start()
