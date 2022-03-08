import argparse
import logging
import os
import urllib.error
import urllib.request

import openfreebuds_applet
import openfreebuds_backend
from openfreebuds import event_bus, device_names, manager, cli_io
from openfreebuds.events import EVENT_MANAGER_STATE_CHANGED
from openfreebuds_applet import tools, tool_server
from openfreebuds_applet.l18n import t

log_format = "%(levelname)s:%(name)s:%(threadName)s  %(message)s"
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
    if args.command != "":
        do_command(args.command)
        return

    if args.shell:
        run_shell()
        return

    version, debug = tools.get_version()
    print("openfreebuds version=" + version + " is_debug=" + str(debug))

    setup_logging(debug)
    start_applet()


def do_command(command):
    port = tool_server.get_port()

    try:
        url = "http://localhost:{}/{}".format(port, command)

        with urllib.request.urlopen(url) as f:
            print(f.read().decode("utf8"))

    except urllib.error.URLError:
        print("Failed. Check that app started and web-server is active.")


# noinspection PyUnresolvedReferences,PyProtectedMember
def start_applet():
    if tools.is_running():
        openfreebuds_backend.show_message(t("application_running_message"),
                                          callback=lambda: os._exit(0))
        openfreebuds_backend.ui_lock()
    openfreebuds_applet.start()


def setup_logging(debug):
    if args.verbose or debug:
        print("Enabled verbose mode")
        logging.basicConfig(level=logging.DEBUG, format=log_format, force=True)
    else:
        logfile = tools.get_log_filename()
        print("Log redirected to file " + logfile + ". Set --verbose flag to see logs here.")
        logging.basicConfig(level=logging.DEBUG, format=log_format, filename=logfile)

    logging.getLogger("asyncio").disabled = True


def run_shell():
    man = manager.create()

    if args.verbose:
        print("Enabled verbose mode")
        logging.basicConfig(level=logging.DEBUG, format=log_format, force=True)

    print("-- Scan feature test:")
    devices = openfreebuds_backend.bt_list_devices()
    for i, a in enumerate(devices):
        print(i, a["name"], "(" + a["address"] + ")", a["connected"])
    print()

    num = int(input("Enter device num to use: "))
    name = devices[num]["name"]
    address = devices[num]["address"]

    if not device_names.is_supported(name):
        print("!! Device with this name isn't tested.")
        print("!! It can work incorrectly with this app")
        if not input("Type yes to continue: ").lower() == "yes":
            print("bye")
            raise SystemExit
    print()

    print("-- Using device", address)
    man.set_device(address)

    while True:
        print("-- Waiting for spp connect...")
        while man.state != man.STATE_CONNECTED:
            event_bus.wait_for(EVENT_MANAGER_STATE_CHANGED)

        logging.getLogger("CLI-IO").disabled = True
        shell(man)
        print("-- Device disconnected")


def shell(mgr):
    while not mgr.device.closed:
        command = input("OpenFreebuds> ").split(" ")

        if command[0] == "":
            continue

        if command[0] == "q":
            mgr.close()
            print('bye')
            raise SystemExit

        print(cli_io.dev_command(mgr, command))


tools.run_safe(main, "MainThread", True)
