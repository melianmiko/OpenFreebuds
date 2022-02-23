import json
import logging
import threading

from openfreebuds_applet import tools
from http.server import HTTPServer, SimpleHTTPRequestHandler

log = logging.getLogger("Webserver")


class Config:
    applet = None
    port = 21201


class AppHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path

        if path.startswith("/properties"):
            return self.get_props()
        elif path.startswith("/next_mode"):
            return self.next_mode()
        elif path.startswith("/mode_0"):
            return self.set_mode(0)
        elif path.startswith("/mode_1"):
            return self.set_mode(1)
        elif path.startswith("/mode_2"):
            return self.set_mode(2)
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
            return "No device", 501

        return self._answer_json(man.device.list_properties(), 200)

    def next_mode(self):
        man = Config.applet.manager
        if not man.state == man.STATE_CONNECTED:
            return self._answer_json({"error": "No device"}, 501)

        dev = man.device
        current = dev.get_property("noise_mode", -99)
        if current == -99:
            return self._answer_json({"error": "Not supported"}, 501)

        new_mode = (current + 1) % 3
        dev.set_property("noise_mode", new_mode)
        log.debug("Switched to mode " + str(new_mode))

        return self._answer_json(True, 200)

    def set_mode(self, mode):
        man = Config.applet.manager
        if not man.state == man.STATE_CONNECTED:
            return self._answer_json({"error": "No device"}, 501)

        man.device.set_property("noise_mode", mode)
        log.debug("Switched to mode " + str(mode))

        return self._answer_json(True, 200)


def start(applet):
    Config.applet = applet

    if not applet.settings.enable_server:
        return

    httpd = HTTPServer(("localhost", Config.port), AppHandler)
    threading.Thread(target=httpd.serve_forever).start()
    log.info("Running webserver for localhost, port is " + str(Config.port))


def get_port():
    return Config.port
