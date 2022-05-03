import platform
import traceback
import json

import openfreebuds_backend
from version_info import VERSION
from openfreebuds_applet import utils

report_header = """
========================================================================
This is self-check report, created via OpenFreebuds.
SAVE this file and send them to developer, if you have some troubles.
========================================================================

"""


def generate_report(applet):
    report = report_header

    report += ("version: {}".format(VERSION)) + "\n"
    report += ("platform: {} {}".format(platform.system(), platform.release())) + "\n"
    report += "\n"

    # Settings
    try:
        report += ("-- settings file\n")
        with open(utils.get_settings_path(), "r") as f:
            settings = json.loads(f.read())
            report += json.dumps(settings, indent=2) + "\n"
    except Exception:
        report += "failed to read settings file\n"
        report += traceback.format_exc() + "\n"
    report += "\n"

    # Backend
    try:
        report += '-- Backend tests\n'

        report += "bt_list_devices:\n"
        devices = openfreebuds_backend.bt_list_devices()
        report += json.dumps(devices, indent=2) + "\n"
    except Exception:
        report += "failed to process backend tests\n"
        report += traceback.format_exc() + "\n"
    report += "\n"

    # Device
    try:
        report += '-- Device tests\n'
        report += "state: {}\n".format(applet.manager.state)
        device = applet.manager.device

        report += "props:\n"
        report += json.dumps(device.list_properties(), indent=2) + "\n"
    except Exception:
        report += "failed to process device tests\n"
        report += traceback.format_exc() + "\n"
    report += "\n"

    # Log
    report += "-- Debug log\n"
    report += applet.log.getvalue()

    return report
