import json
import logging
import time
import urllib.request
import urllib.error

from openfreebuds_applet import utils
from http.server import HTTPServer, SimpleHTTPRequestHandler

from openfreebuds_applet.modules import actions

log = logging.getLogger("Webserver")


class Config:
    started = False
    httpd = None
    applet = None
    actions = {}
    port = 21201


class AppHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path

        if path.startswith("/properties"):
            return self.get_props()
        elif path.replace("/", "") in Config.actions:
            return self.do_action()
        else:
            return self.info()

    def _answer_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf8"))

    def _answer_html_file(self, path, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open(path, "rb") as f:
            self.wfile.write(f.read())

    def info(self):
        return self._answer_html_file(utils.get_assets_path() + "/server_help.html", 200)

    def get_props(self):
        man = Config.applet.manager
        if not man.state == man.STATE_CONNECTED:
            return self._answer_json(False, 501)

        return self._answer_json(man.device.list_properties(), 200)

    def do_action(self):
        name = self.path.replace("/", "")
        result = Config.actions[name]()
        if result:
            return self._answer_json(True, 200)
        else:
            return self._answer_json(False, 501)


def start(applet):
    Config.applet = applet
    Config.actions = actions.get_actions(applet)

    if Config.started:
        try:
            Config.started = False
            urllib.request.urlopen("http://localhost:{}".format(Config.port))
        except urllib.error.URLError:
            pass

    if applet.settings.enable_server:
        applet.run_thread(_httpd_thread, "HTTPServer", False)


def _httpd_thread():
    while Config.httpd is not None:
        log.debug("waiting for stop")
        time.sleep(1)

    host = "localhost"
    if Config.applet.settings.server_access:
        log.warning("Enable global access")
        host = "0.0.0.0"

    Config.httpd = HTTPServer((host, Config.port), AppHandler)
    Config.started = True

    log.info("Running webserver for localhost, port is " + str(Config.port))

    while Config.started:
        Config.httpd.handle_request()

    Config.httpd.server_close()
    Config.httpd = None
    log.info("Closed webserver")


def get_port():
    return Config.port
