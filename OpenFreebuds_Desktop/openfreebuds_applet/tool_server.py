import logging
import threading

from flask import Flask, send_file

from openfreebuds_applet import tools

applet = None
server = Flask(__name__)
log = logging.getLogger("Webserver")
port = 21201


@server.route("/")
def info():
    return send_file(tools.get_assets_path() + "/server_help.html")


# noinspection PyUnresolvedReferences
@server.route("/properties")
def get_props():
    man = applet.manager
    if not man.state == man.STATE_CONNECTED:
        return "No device", 501

    return man.device.list_properties(), 200


# noinspection PyShadowingNames,PyUnresolvedReferences
@server.route("/next_mode")
def next_mode():
    man = applet.manager
    if not man.state == man.STATE_CONNECTED:
        return "No device", 501

    dev = man.device
    current = dev.get_property("noise_mode", -99)
    if current == -99:
        return "Not supported", 501
    next_mode = (current + 1) % 3
    dev.set_property("noise_mode", next_mode)
    log.debug("Switched to mode " + str(next_mode))

    return "OK", 200


def start(applet_):
    global applet
    applet = applet_

    if not applet.settings.enable_flask:
        return

    threading.Thread(target=server.run, args=("127.0.0.1", port, False)).start()
    log.info("Running webserver for localhost, port is " + str(port))
