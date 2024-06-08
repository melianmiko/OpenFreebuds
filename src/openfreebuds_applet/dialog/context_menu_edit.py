import tkinter
from tkinter import ttk

from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet.l18n import t
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools


class ContextMenuEditDialog(tkinter.Toplevel):
    def __init__(self, settings: SettingsStorage):
        super().__init__(class_="openfreebuds")
        self.wm_title(t("Context menu..."))
        self.wm_geometry("400x400")
        self.wm_resizable(False, False)

        self.settings = settings
        self.vars = {}

        self.add_item("equalizer", t("Equalizer"))
        self.add_item("dual_connect", t("Dual-connection"))

    def add_item(self, option_id: str, display_name: str):
        self.vars[option_id] = tkinter.BooleanVar(value=option_id in self.settings.context_menu_extras)

        def _toggle():
            if self.vars[option_id].get():
                self.settings.context_menu_extras.append(option_id)
            else:
                self.settings.context_menu_extras.remove(option_id)
            self.settings.write()
            event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

        ttk.Checkbutton(self, text=display_name,
                        variable=self.vars[option_id],
                        command=_toggle)\
            .grid(sticky=tkinter.NW, padx=16, pady=8)


@tk_tools.ui_thread
def start(settings: SettingsStorage):
    window = ContextMenuEditDialog(settings)
    window.mainloop()
