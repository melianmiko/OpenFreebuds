#!/usr/bin/python3

import argparse
import logging
import os
import socket
import sys
import time
import urllib.error
import urllib.request

import openfreebuds_applet
import openfreebuds_backend
import psutil
from openfreebuds import cli_io
from openfreebuds.utils import event_bus
from openfreebuds.constants.events import EVENT_MANAGER_STATE_CHANGED, EVENT_DEVICE_PROP_CHANGED
from openfreebuds.utils.logger import create_log
from openfreebuds.main import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules.actions import get_actions
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools

log = create_log("OfbLauncher")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Unofficial application to manage HUAWEI FreeBuds device")

    parser.add_argument("--verbose",
                        default=False, action="store_true",
                        help="Print debug log to console")
    parser.add_argument("--shell",
                        default=False, action="store_true",
                        help="Start CLI shell instead of applet")
    parser.add_argument("--settings",
                        default=False, action="store_true",
                        help="Show settings dialog after app initialization")
    parser.add_argument("--connection-center",
                        default=False, action="store_true",
                        help="Show connection manager dialog after app initialization")
    parser.add_argument("command",
                        default="", type=str, nargs='?',
                        help="If provided, will send command to httpserver and exit")
    return parser.parse_args()


def is_running():
    # This is temporary
    # This is temporary
    # This is temporary

    our_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.pid == our_pid:
            continue

        try:
            cmdline = proc.cmdline()
        except psutil.Error:
            continue

        running = False
        if sys.platform == "win32" and len(cmdline) > 0:
            running = cmdline[0].endswith("openfreebuds.exe")
        elif len(cmdline) > 1:
            running = cmdline[1] == "/usr/bin/openfreebuds" or "ofb_launcher.py" in cmdline[1]

        if running:
            log.info(f"Found exiting instance, {proc}")
            return True

    return False


def main():
    args = parse_args()

    # Setup logging
    logging.getLogger("asyncio").disabled = True
    logging.getLogger("CLI-IO").disabled = True
    logging.basicConfig(level=logging.DEBUG, format=openfreebuds_applet.log_format, force=True)

    if args.command != "":
        do_command(args.command)
        return
    elif args.shell:
        run_shell()
        return

    applet = openfreebuds_applet.create()
    applet.on_device_available = lambda: on_device_available(applet, args)
    if is_start_possible():
        # Start is allowed, running
        applet.start()
    else:
        # Run main thread to make windows interactive
        applet.tray_application.run()


def on_device_available(applet, args):
    if args.settings:
        from openfreebuds_applet.ui.settings_ui import open_app_settings
        open_app_settings(applet)
    if args.connection_center:
        from openfreebuds_applet.dialog import connection_center
        connection_center.start(applet.manager.device)


def is_start_possible():
    # Is already running?
    if is_running():
        tk_tools.message(
            t("Application already running, check status area.\n\n "
              "If app don't response, stop it from system task manager, \n"
              "and then try again."),
            "Error", _leave)
        return False

    # Is python built with AF_BLUETOOTH support?
    if not getattr(socket, "AF_BLUETOOTH", False):
        tk_tools.message(t("Current Python interpreter didn't support Bluetooth.\n\n"
                           "Some variants of Python 3 are compiled without BT socket\n"
                           "support, and this application won't work on them. Please\n"
                           "use standard Python 3.10 or newer to run OFB."),
                         "Error",
                         _leave)
        return False

    # Is bluetooth adapter accessible
    # try:
    #     openfreebuds_backend.bt_list_devices()
    # except BluetoothNotAvailableError:
    #     tk_tools.message(t("no_bluetooth_error"), "Error", _leave)
    #     return False

    return True


def do_command(command):
    if is_running():
        log.debug("App is launched, using HTTP server to process command...")
        _do_command_webserver(command)
    else:
        log.debug("App isn't launched, trying to run command without them")
        _do_command_offline(command)


def _do_command_webserver(command):
    port = 21201

    try:
        url = "http://localhost:{}/{}".format(port, command)

        with urllib.request.urlopen(url) as f:
            print(f.read().decode("utf8"))

    except urllib.error.URLError:
        log.exception("Can't do command via HTTP-server")
        tk_tools.message(t("Can't execute command. Check that command is valid and \n"
                           "that \"Remote control server\" is enabled in OpenFreebuds settings."),
                         "Openfreebuds",
                         _leave)


def _do_command_offline(command):
    man = FreebudsManager.get()
    settings = SettingsStorage()
    if settings.address == "":
        log.error("No saved device, bye")
        return

    start = time.time()
    man.set_device(settings.device_name, settings.address)
    while man.state != man.STATE_CONNECTED and man.state != man.STATE_OFFLINE:
        if time.time() - start > 5:
            log.debug("connection timed out, bye")
            _leave()
        time.sleep(0.25)

    log.debug("ready to run")
    actions = get_actions(man)
    if command not in actions:
        log.error("Undefined command")
        _leave()

    actions[command]()
    event_bus.wait_for(EVENT_DEVICE_PROP_CHANGED, timeout=2)
    print("true")
    _leave()


def _leave():
    # noinspection PyProtectedMember,PyUnresolvedReferences
    os._exit(1)


def run_shell():
    man = FreebudsManager.get()

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
