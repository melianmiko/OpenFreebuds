import asyncio
import traceback
from typing import Optional

from PIL import ImageQt
from PyQt6.QtGui import QIcon

from openfreebuds import IOpenFreebuds
from openfreebuds.exceptions import FbServerDeadError
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config import get_openfreebuds_qt_config, get_tray_icon_theme
from openfreebuds_qt.generic import IOfbQtMainWindow
from openfreebuds_qt.tray.generic import IOfbTrayIcon
from openfreebuds_qt.tray.icon import create_tray_icon
from openfreebuds_qt.tray.menu import OfbDeviceOnlineTrayMenu, OfbCommonTrayMenu

UI_UPDATE_GROUPS = ["anc", "battery"]
log = create_logger("OfbTrayIcon")


class OfbTrayIcon(IOfbTrayIcon):
    """
    OpenFreebuds Tray icon implementation
    """

    def __init__(self, root: IOfbQtMainWindow):
        super().__init__(root)

        self.root = root
        self.ofb = root.ofb

        self.ui_update_task: Optional[asyncio.Task] = None
        self.menu_current: Optional[OfbCommonTrayMenu] = None

        self.test_menu = OfbCommonTrayMenu(self.root, self)
        self.menu_device = OfbDeviceOnlineTrayMenu(self.root, self)

    async def boot(self):
        """
        Will start UI update loop and perform other preparations on boot
        """
        if self.ui_update_task is None:
            self.ui_update_task = asyncio.create_task(self._update_loop())

        await self._update_ui()

    async def close(self):
        """
        Will stop UI update loop
        """
        if self.ui_update_task is not None:
            self.ui_update_task.cancel()
            await self.ui_update_task
            self.ui_update_task = None

    async def _update_ui(self, kind: str = "", *args):
        """
        UI update callback
        """

        state = await self.ofb.get_state()

        # Update icon
        icon = create_tray_icon(get_tray_icon_theme(),
                                state,
                                await self.ofb.get_property("battery", "global", 0),
                                await self.ofb.get_property("anc", "mode", "normal"))
        pixmap = QIcon(ImageQt.toqpixmap(icon))
        self.setIcon(pixmap)

        # Update menu
        if state == IOpenFreebuds.STATE_CONNECTED:
            target_menu = self.menu_device
        else:
            target_menu = self.test_menu

        if self.menu_current != target_menu:
            self.setContextMenu(target_menu)
            self.menu_current = target_menu
            await self.menu_current.on_attach()
        elif kind == "put_property":
            await self.menu_current.on_core_property_change(*args)

    async def _update_loop(self):
        """
        Background task that will subscribe to core event bus and watch
        for changes to perform tray UI update when something changes.
        """

        member_id = await self.ofb.subscribe()
        log.info(f"Tray update loop started, member_id={member_id}")

        try:
            while True:
                kind, *args = await self.ofb.wait_for_event(member_id)
                if kind == "state_changed" and args[0] == IOpenFreebuds.STATE_DESTROYED:
                    raise FbServerDeadError("Server going to exit")
                if kind == "state_changed" or (kind == "put_property" and args[0] in UI_UPDATE_GROUPS):
                    await self._update_ui(kind, *args)
        except asyncio.CancelledError:
            await self.ofb.unsubscribe(member_id)
        except FbServerDeadError:
            log.info("Server is dead, exiting now...")
            self.ui_update_task = None
            await self.root.exit(1)

    def setContextMenu(self, menu: OfbCommonTrayMenu):
        self.menu_current = menu
        super().setContextMenu(menu)
