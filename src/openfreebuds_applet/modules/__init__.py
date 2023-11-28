import importlib
import logging
from pkgutil import walk_packages

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.modules.generic import GenericModule, FailedModule
from openfreebuds_applet.settings import SettingsStorage

log = logging.getLogger("ModuleManager")


class ModuleManager:
    def __init__(self, settings: SettingsStorage, manager: FreebudsManager):
        self.modules: dict[str, GenericModule] = {}
        self._app_settings = settings
        self._app_manager = manager
        self._load()

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
        log.info(self.modules)
        for ident in self.modules:
            if self.modules[ident].get_property("enabled"):
                self.modules[ident].start()
