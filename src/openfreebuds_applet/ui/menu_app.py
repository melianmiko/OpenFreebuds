from pystrayx import Menu

from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import settings_ui
from openfreebuds_applet.dialog import device_select


class ApplicationMenuPart(Menu):
    """
    Base application settings_ui menu part.
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        self.add_separator()

        self.add_item(t("action_settings"), self.open_settings)
        self.add_item(t("action_select_device"), self.open_device_picker)
        self.add_item(t("action_exit"), self.applet.exit)

    def open_device_picker(self):
        device_select.start(self.applet.settings, self.applet.manager)

    def open_settings(self):
        settings_ui.open_app_settings(self.applet)
