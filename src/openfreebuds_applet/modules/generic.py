import logging
import tkinter
from copy import deepcopy

from openfreebuds.logger import create_log
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage

log = create_log("AppletModule")


class GenericModule:
    ident: str = ""
    name: str = ""
    description: str = ""
    order: int = 99
    hidden: bool = False
    has_settings_ui: bool = False
    crashed: bool = False
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

    @property
    def settings(self):
        return self.app_settings.modules[self.ident]

    def get_property(self, key: str, fallback: any = None) -> any:
        if key not in self.settings:
            return fallback
        return self.settings[key]

    def set_property(self, key: str, value: any):
        self.settings[key] = value
        self.app_settings.write()

    @utils.async_with_ui("Module")
    def start(self):
        log.info(f"Starting module {self.ident}")
        self.running = True

        self._mainloop()

        log.info(f"Module {self.ident} exited.")
        self.running = False

    def stop(self):
        self.running = False

    def _mainloop(self):
        pass

    def make_settings_frame(self, parent: tkinter.BaseWidget) -> tkinter.Frame | None:
        f = tkinter.Frame(parent)
        tkinter.Label(f, text=t("This module don't have any options")).pack()
        return f


class FailedModule(GenericModule):
    crashed = True

    def __init__(self, ident, error):
        super().__init__()
        self.ident = ident
        self.name = ident
        self.description = error

    def get_property(self, key: str, fallback: any = None) -> any:
        return fallback
