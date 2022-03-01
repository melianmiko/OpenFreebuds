import json
import logging

from openfreebuds_applet import tools, tool_actions
from http.server import HTTPServer, SimpleHTTPRequestHandler

log = logging.getLogger("Webserver")


class Config:
    current = None
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
        return self._answer_html_file(tools.get_assets_path() + "/server_help.html", 200)

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
    Config.actions = tool_actions.get_actions(applet)

    if Config.current is not None:
        Config.current.server_close()
        log.info("Server closed")

    if not applet.settings.enable_server:
        return

    httpd = HTTPServer(("localhost", Config.port), AppHandler)
    tools.run_thread_safe(httpd.serve_forever, "HTTPServer", False)
    Config.current = httpd

    log.info("Running webserver for localhost, port is " + str(Config.port))


def get_port():
    return Config.port
