import logging
import time
import tkinter
import urllib.error
import urllib.request
from http.server import HTTPServer

from openfreebuds.logger import create_log
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import GenericModule
from openfreebuds_applet.modules.actions import get_actions
from openfreebuds_applet.modules.http_server._handler import AppHandler
from openfreebuds_applet.modules.http_server._settings import WebServerSettings

log = create_log("Webserver")


class Module(GenericModule):
    ident = "http_server"
    name = t("module_http_server")
    description = t("http_server_info")
    order = 1
    has_settings_ui = True
    def_settings = {
        "enabled": False,
        "external_access": False,
        "port": 21201
    }

    def __init__(self):
        super().__init__()
        self.httpd = None

    def _mainloop(self):
        while self.httpd is not None:
            log.debug("waiting for stop")
            time.sleep(1)

        host = "localhost"
        if self.get_property("external_access"):
            host = "0.0.0.0"

        AppHandler.manager = self.app_manager
        AppHandler.actions = get_actions(self.app_manager)

        port = self.get_property("port")
        self.httpd = HTTPServer((host, port), AppHandler)

        log.info(f"Running webserver for {host}, port is {port}")

        while self.running:
            self.httpd.handle_request()

        self.httpd.server_close()
        self.httpd = None
        log.info("Closed webserver")

    def stop(self):
        super().stop()
        try:
            urllib.request.urlopen("http://localhost:{}".format(self.get_property("port")))
        except urllib.error.URLError:
            pass

    def make_settings_frame(self, parent: tkinter.BaseWidget) -> tkinter.Frame | None:
        return WebServerSettings(parent, self)
