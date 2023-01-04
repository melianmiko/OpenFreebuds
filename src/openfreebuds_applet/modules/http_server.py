import json
import logging
import time
import urllib.request
import urllib.error

from openfreebuds_applet import utils
from http.server import HTTPServer, SimpleHTTPRequestHandler

from openfreebuds_applet.modules import actions

log = logging.getLogger("Webserver")
base_help_template = utils.get_assets_path() + "/server_help.html"
help_item_pattern = """<section>
<div class="method">GET</div>
<div class="url">/{}</div>
<div class="info">{}</div>
</section>"""


class Config:
    started = False
    httpd = None
    applet = None
    actions = {}
    port = 21201


def generate_help():
    with open(base_help_template, "r") as f:
        data = f.read()

    labels = actions.get_action_names()
    content = ""
    for action_name in labels:
        content += help_item_pattern.format(action_name, labels[action_name])

    return data.replace("{items}", content)


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

    def info(self):
        data = generate_help()

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(data.encode("utf8"))

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
            return self._answer_json(False, 502)


def start(applet):
    Config.applet = applet
    Config.actions = actions.get_actions(applet.manager)

    if Config.started:
        try:
            Config.started = False
            urllib.request.urlopen("http://localhost:{}".format(Config.port))
        except urllib.error.URLError:
            pass

    if applet.settings.enable_server:
        _httpd_thread()


@utils.async_with_ui("HTTPServer")
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
