import json
import platform
import sys
from contextlib import suppress

import openfreebuds_backend
from openfreebuds.utils.logger import get_full_log
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.config.config_lock import ConfigLock
from openfreebuds_qt.constants import STORAGE_PATH
from openfreebuds_qt.generic import IOfbQtApplication
from openfreebuds_qt.version_info import VERSION

REPORT_HEADER = """
   _____             _____             _         _     
  |     |___ ___ ___|   __|___ ___ ___| |_ _ _ _| |___ 
  |  |  | . | -_|   |   __|  _| -_| -_| . | | | . |_ -|
  |_____|  _|___|_|_|__|  |_| |___|___|___|___|___|___|
        |_|                                            
"""
REPORT_CONTACT_DATA = "E-Mail: support@mmk.pw  -or-  Web: https://mmk.pw/en/mailto"
REPORT_INTRO_DEFAULT = """
If you feel that something don't work as expected, please,
    save this file somewhere and send it to developer.
"""
REPORT_INTRO_CRASH = """
         OpenFreebuds crashed due to unknown error.

  If you don't know why this happened, you could try to
   send this log to developer, and they will try to do
  something to prevent this failure in future versions.
"""


class OfbQtReportTool:
    def __init__(self, ctx: IOfbQtApplication, is_crash=False):
        self.is_crash = is_crash
        self.ctx = ctx
        self.config = OfbQtConfigParser.get_instance()
        self.content = ""

    async def create_report(self):
        self.content = REPORT_HEADER

        self.append(REPORT_INTRO_DEFAULT if not self.is_crash else REPORT_INTRO_CRASH)
        self.append(REPORT_CONTACT_DATA)
        self.header("Release info")
        self.append(
            f"version={VERSION}",
            f"os_platform={platform.system()}-{platform.release()}",
            f"python={sys.version_info}"
        )

        self.header("Role info")
        self.append(
            f"core_role={self.ctx.ofb.role}",
            f"config_lock_owned={ConfigLock.owned}",
        )

        with suppress(Exception):
            self.header("Configuration file")
            self.append(json.dumps(self.config.data, indent=2))

        with suppress(Exception):
            self.header("Core health report")
            self.append(json.dumps(await self.ctx.ofb.get_health_report(), indent=2))

        if self.ctx.ofb.role != "standalone":
            self.header("Core server log")
            with suppress(Exception):
                self.append(await self.ctx.ofb.get_logs())

        self.header("Current process log")
        self.append(get_full_log())

        return self.content

    async def create_and_show(self):
        await self.create_report()

        path = STORAGE_PATH / ".OpenFreebuds_report.log"
        with open(path, "w") as f:
            f.write(self.content)
        openfreebuds_backend.open_file(path)

    def header(self, header):
        self.append("", f"=== {header} ===")

    def append(self, *args):
        self.content += "\n".join(args) + "\n"
