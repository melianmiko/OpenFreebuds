import asyncio
from typing import Optional

from PIL import ImageQt
from PyQt6.QtGui import QIcon

from openfreebuds.exceptions import FbServerDeadError
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config import get_openfreebuds_qt_config, get_tray_icon_theme
from openfreebuds_qt.generic import IOfbQtMainWindow
from openfreebuds_qt.tray.generic import IOfbTrayIcon
from openfreebuds_qt.tray.icon import create_tray_icon
from openfreebuds_qt.tray.menu.common import OfbCommonTrayMenu

UI_UPDATE_GROUPS = ["anc", "battery"]


class OfbTrayIcon(IOfbTrayIcon):
    """
    OpenFreebuds Tray icon implementation
    """

    def __init__(self, root: IOfbQtMainWindow):
        super().__init__(root)

        self.root = root
        self.ofb = root.ofb

        self.ui_update_task: Optional[asyncio.Task] = None

        self.current_menu: Optional[OfbCommonTrayMenu] = None
        self.test_menu = OfbCommonTrayMenu(self.root, self)

        self.setContextMenu(self.test_menu)

    async def boot(self):
        """
        Will start UI update loop and perform other preparations on boot
        """
        if self.ui_update_task is None:
            self.ui_update_task = asyncio.create_task(self._update_loop())

        await self._update_ui()
        await self.test_menu.build()

    async def close(self):
        """
        Will stop UI update loop
        """
        if self.ui_update_task is not None:
            self.ui_update_task.cancel()
            await self.ui_update_task

    async def _update_ui(self):
        """
        UI update callback
        """

        icon = create_tray_icon(get_tray_icon_theme(),
                                await self.ofb.get_state(),
                                await self.ofb.get_property("battery", "global", 0),
                                await self.ofb.get_property("anc", "mode", "normal"))
        pixmap = QIcon(ImageQt.toqpixmap(icon))
        self.setIcon(pixmap)

        if self.current_menu:
            await self.current_menu.build()

    async def _update_loop(self):
        """
        Background task that will subscribe to core event bus and watch
        for changes to perform tray UI update when something changes.
        """

        member_id = await self.ofb.subscribe()

        try:
            while True:
                kind, group, *_ = await self.ofb.wait_for_event(member_id)
                if kind == "state_changed" or (kind == "put_property" and group in UI_UPDATE_GROUPS):
                    await self._update_ui()
        except asyncio.CancelledError:
            await self.ofb.unsubscribe(member_id)
        except FbServerDeadError:
            await self.root.exit(1)

    def setContextMenu(self, menu: OfbCommonTrayMenu):
        self.current_menu = menu
        super().setContextMenu(menu)
