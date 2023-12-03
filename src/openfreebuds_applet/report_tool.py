import json
import platform
import sys
import traceback

import openfreebuds_backend
from openfreebuds import logger
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet import utils
from version_info import VERSION


report_header = """
   _____             _____             _         _     
  |     |___ ___ ___|   __|___ ___ ___| |_ _ _ _| |___ 
  |  |  | . | -_|   |   __|  _| -_| -_| . | | | . |_ -|
  |_____|  _|___|_|_|__|  |_| |___|___|___|___|___|___|
        |_|                                            
"""

contact_data = "E-Mail: support@mmk.pw  -or-  Web: https://mmk.pw/en/mailto"

report_intro = {

    "default": """
If you feel that something don't work as expected, please,
    save this file somewhere and send it to developer.
""",

    "crash": """
         OpenFreebuds crashed due to unknown error.

  If you don't know why this happened, you coul'd try to
   send this log to developer, and they will try to do
  something to prevent this failure in future versions.
"""
}


def create_and_show(intro_style="default"):
    path = utils.get_app_storage_dir() / ".OpenFreebuds_report.log"
    report = create(intro_style)
    with open(path, "w") as f:
        f.write(report)
    openfreebuds_backend.open_file(path)


# noinspection PyBroadException
def create(intro_style="default"):
    manager = FreebudsManager.get()
    report = (f"{report_header}\n"
              f"{report_intro[intro_style]}\n"
              f"{contact_data}\n"
              f"\n"
              f"app_version={VERSION}\n"
              f"python_version={sys.version_info}\n"
              f"os_platform={platform.system()}-{platform.release()}\n"
              f"\n")

    # Settings
    report += "-= Settings file =-\n"
    try:
        path = utils.get_app_storage_dir() / "settings.json"
        with open(path, "r") as f:
            settings = json.loads(f.read())
            report += json.dumps(settings, indent=2) + "\n"
    except Exception:
        report += traceback.format_exc() + "\n"
    report += "\n"

    # Device
    report += (f"-= Manager state =-\n"
               f"device_name={manager.device_name}\n"
               f"device_addr={manager.device_address}\n"
               f"state={manager.state}\n"
               f"device_class={manager.device}\n"
               f"\n")

    report += f"-= Device state =-\n"
    try:
        report += json.dumps(manager.device.list_properties(), indent=2) + "\n"
    except Exception:
        report += traceback.format_exc() + "\n"
    report += "\n"

    # Log
    report += "-= Entire application log =-\n"
    report += logger.get_full()

    return report
