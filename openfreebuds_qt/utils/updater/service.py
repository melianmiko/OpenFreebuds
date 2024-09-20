import sys
from typing import Optional

from PyQt6.QtWidgets import QWidget

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.constants import STORAGE_PATH
from openfreebuds_qt.version_info import VERSION

try:
    from mmk_updater import UpdateCheckerConfig
    from mmk_updater.qt import MmkUpdaterQt
except ImportError:
    UpdateCheckerConfig = None
    MmkUpdaterQt = None

log = create_logger("OfbQtUpdaterService")


class OfbQtUpdaterService:
    def __init__(self, parent: QWidget):
        self.config = OfbQtConfigParser.get_instance()

        is_win32 = sys.platform == "win32"
        mode = self.config.get("updater", "mode", "show")

        if UpdateCheckerConfig is not None and MmkUpdaterQt is not None:
            self.updater_config = UpdateCheckerConfig(
                server_url="https://st.mmk.pw/openfreebuds",
                current_version=VERSION,
                state_location=STORAGE_PATH / "qt_updater.json",
                app_display_name="OpenFreebuds",
                notify_method=(UpdateCheckerConfig.NotifyMethod.POP_UP
                               if is_win32 and mode == "show"
                               else UpdateCheckerConfig.NotifyMethod.NONE)
            )
            self.updater = MmkUpdaterQt(parent, self.updater_config)    # type: MmkUpdaterQt
        else:
            self.updater_config = None
            self.updater = None                                         # type: MmkUpdaterQt

    async def boot(self):
        if UpdateCheckerConfig is None:
            log.info("Skip, unavailable")
            return

        if self.config.get("updater", "mode", "show") == "off":
            return

        if "git" in VERSION:
            return

        await self.updater.boot()

    async def check_now(self):
        await self.updater.check_now(True)
