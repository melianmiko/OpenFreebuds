import logging
from copy import deepcopy

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet import utils
from openfreebuds_applet.settings import SettingsStorage

log = logging.getLogger("AppletModule")


class GenericModule:
    ident: str = ""
    name: str = ""
    description: str = ""
    hidden: bool = False
    os_filter: list[str] | None = None
    def_settings: dict[str, any] = {
        "enabled": False
    }

    def __init__(self):
        self.app_settings: SettingsStorage | None = None
        self.app_manager: FreebudsManager | None = None
        self.running = False

    def connect(self, settings: SettingsStorage, manager: FreebudsManager):
        self.app_settings = settings
        self.app_manager = manager

        # Sync settings
        if self.ident not in settings.modules:
            settings.modules[self.ident] = deepcopy(self.def_settings)
            return True
        changed = False
        for key in self.def_settings:
            if key not in settings.modules[self.ident]:
                settings.modules[self.ident][key] = self.def_settings[key]
                changed = True
        return changed

    def get_property(self, key: str, fallback: any = None) -> any:
        settings = self.app_settings.modules[self.ident]
        if key not in settings:
            return fallback
        return settings[key]

    def set_property(self, key: str, value: any):
        settings = self.app_settings.modules[self.ident]
        settings[key] = value
        self.app_settings.write()

    @utils.async_with_ui("Module")
    def start(self):
        log.info(f"Starting module {self.ident}")
        self.running = True

        self.mainloop()

        log.info(f"Module {self.ident} exited.")
        self.running = False

    def stop(self):
        self.running = False

    def mainloop(self):
        pass


