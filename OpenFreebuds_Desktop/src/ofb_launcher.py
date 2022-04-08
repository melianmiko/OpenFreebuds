import argparse
import logging
import os
import urllib.error
import urllib.request

import openfreebuds_applet
import openfreebuds_backend
from openfreebuds import event_bus, manager, cli_io
from openfreebuds.constants.events import EVENT_MANAGER_STATE_CHANGED
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import http_server


def parse_args():
    parser = argparse.ArgumentParser(
        description="Unofficial application to manage HUAWEI FreeBuds device")

    parser.add_argument("--verbose",
                        default=False, action="store_true",
                        help="Print debug log to console")
    parser.add_argument("--shell",
                        default=False, action="store_true",
                        help="Start CLI shell instead of applet")
    parser.add_argument("command",
                        default="", type=str, nargs='?',
                        help="If provided, will send command to httpserver and exit")
    return parser.parse_args()


# noinspection PyUnresolvedReferences,PyProtectedMember
def main():
    args = parse_args()

    # Setup logging
    logging.getLogger("asyncio").disabled = True
    logging.getLogger("CLI-IO").disabled = True
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=openfreebuds_applet.log_format, force=True)

    if args.command != "":
        do_command(args.command)
        return
    elif args.shell:
        run_shell()
        return

    applet = openfreebuds_applet.create()
    if utils.is_running():
        applet.tray_application.message_box(t("application_running_message"), "Error",
                                            lambda: os._exit(1))
        applet.tray_application.run()
        return

    applet.start()


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

            print(cli_io.dev_command(man.device, command))
        print("-- Device disconnected")


if __name__ == "__main__":
    main()
