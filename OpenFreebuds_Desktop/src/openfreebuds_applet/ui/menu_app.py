from mtrayapp import Menu

import openfreebuds_backend
from openfreebuds import cli_io
from openfreebuds_applet import utils
from openfreebuds_applet.ui import settings_ui
from openfreebuds_applet.l18n import t


class ApplicationMenuPart(Menu):
    """
    Base application settings_ui menu part.
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        self.add_separator()

        if self.applet.settings.enable_debug_features:
            self.add_item("DEV: Run command", self.do_command)
            self.add_item("DEV: Show logs", self.show_log)
            self.add_separator()

        self.add_item(t("action_settings"), self.open_settings)
        self.add_item(t("action_exit"), self.applet.exit)

    def open_settings(self):
        settings_ui.open_app_settings(self.applet)

    def show_log(self):
        value = self.applet.log.getvalue()
        path = str(utils.get_app_storage_dir()) + "/last_log.txt"
        with open(path, "w") as f:
            f.write(value)

        openfreebuds_backend.open_file(path)

    def do_command(self):
        openfreebuds_backend.ask_string("openfreebuds>", self.on_command)

    def on_command(self, result):
        if result is None or result == "":
            return

        command = result.split(" ")
        result = cli_io.dev_command(self.applet.manager.device, command)
        self.application.message_box(result, "Dev mode")
