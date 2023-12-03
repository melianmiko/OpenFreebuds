import json
import logging
from http.server import SimpleHTTPRequestHandler

from openfreebuds.logger import create_log
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet import utils
from openfreebuds_applet.modules import actions

log = create_log("Webserver")

base_help_template = utils.get_assets_path() + "/server_help.html"
help_item_pattern = """<section>
<div class="method">GET</div>
<div class="url">/{}</div>
<div class="info">{}</div>
</section>"""


def generate_help():
    with open(base_help_template, "r") as f:
        data = f.read()

    labels = actions.get_action_names()
    content = ""
    for action_name in labels:
        content += help_item_pattern.format(action_name, labels[action_name])

    return data.replace("{items}", content)


class AppHandler(SimpleHTTPRequestHandler):
    actions = None
    manager: FreebudsManager = None

    def do_GET(self):
        path = self.path

        if path.startswith("/properties"):
            return self.get_props()
        elif path.replace("/", "") in AppHandler.actions:
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
        man = AppHandler.manager
        if not man.state == man.STATE_CONNECTED:
            return self._answer_json(False, 501)

        return self._answer_json(man.device.list_properties(), 200)

    def do_action(self):
        name = self.path.replace("/", "")
        result = AppHandler.actions[name]()
        if result:
            return self._answer_json(True, 200)
        else:
            return self._answer_json(False, 502)

