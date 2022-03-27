import argparse
import logging
import sys
import urllib.error
import urllib.request

import openfreebuds_applet
import openfreebuds_backend
from openfreebuds import event_bus, manager, cli_io
from openfreebuds.constants.events import EVENT_MANAGER_STATE_CHANGED
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import http_server

description = "Unofficial application to manage HUAWEI FreeBuds device"

parser = argparse.ArgumentParser(description=description)
parser.add_argument("--verbose",
                    default=False, action="store_true",
                    help="Print debug log to console")
parser.add_argument("--shell",
                    default=False, action="store_true",
                    help="Start CLI shell instead of applet")
parser.add_argument("command",
                    default="", type=str, nargs='?',
                    help="If provided, will send command to httpserver and exit")
args = parser.parse_args()


def main():
    version, debug = utils.get_version()
    print("openfreebuds version=" + version + " is_debug=" + str(debug))

    # Setup logging
    logging.getLogger("asyncio").disabled = True
    logging.getLogger("CLI-IO").disabled = True
    if args.verbose or debug:
        logging.basicConfig(level=logging.DEBUG, format=openfreebuds_applet.log_format, force=True)

    if args.command != "":
        do_command(args.command)
    elif args.shell:
        run_shell()
    elif utils.is_running():
        # TODO: Do something with this shit
        openfreebuds_backend.show_message(t("application_running_message"), callback=lambda: sys.exit())
        openfreebuds_backend.ui_lock()
    else:
        openfreebuds_applet.start()


def do_command(command):
    port = http_server.get_port()

    try:
        url = "http://localhost:{}/{}".format(port, command)

        with urllib.request.urlopen(url) as f:
            print(f.read().decode("utf8"))

    except urllib.error.URLError:
        print("Failed. Check that app started and web-server is active.")


def run_shell():
    man = manager.create()

    # Device picker
    devices = openfreebuds_backend.bt_list_devices()
    for i, a in enumerate(devices):
        print(i, a["name"], "(" + a["address"] + ")", a["connected"])
    print()

    num = int(input("Enter device num to use: "))
    name = devices[num]["name"]
    address = devices[num]["address"]

    # Start shell
    print("-- Using device", address)
    man.set_device(name, address)

    while True:
        print("-- Waiting for spp connect...")
        while man.state != man.STATE_CONNECTED:
            event_bus.wait_for(EVENT_MANAGER_STATE_CHANGED)

        while not man.device.closed:
            command = input("OpenFreebuds> ").split(" ")

            if command[0] == "":
                continue

            if command[0] == "q":
                man.close()
                print('bye')
                raise SystemExit

            print(cli_io.dev_command(man, command))
        print("-- Device disconnected")


utils.run_safe(main, "MainThread", True)
