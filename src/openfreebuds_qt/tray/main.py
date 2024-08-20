import asyncio

from PIL import ImageQt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from openfreebuds import OpenFreebuds
from openfreebuds_qt.config import get_openfreebuds_qt_config
from openfreebuds_qt.tray.icon import create_tray_icon


class OfbTrayIcon(QSystemTrayIcon):
    def __init__(self, parent: QWidget, manager: OpenFreebuds):
        super().__init__(parent)
        menu = QMenu(parent)
        menu.addAction("Exit")

        self.ofb = manager
        self.config = get_openfreebuds_qt_config()
        self.ui_update_task: asyncio.Task | None = None

        self.setContextMenu(menu)

    async def boot(self):
        if self.ui_update_task is None:
            self.ui_update_task = asyncio.create_task(self._update_loop())
        await self._update_icon()

    def close(self):
        if self.ui_update_task is not None:
            self.ui_update_task.cancel()

    async def _update_loop(self):
        member_id = await self.ofb.subscribe()

        try:
            while True:
                kind, group, *_ = await self.ofb.wait_for_event(member_id)
                print("E", kind, group)
                if kind == "state_changed" or (kind == "put_property" and group in ["anc", "battery"]):
                    await self._update_icon()
        except asyncio.CancelledError:
            await self.ofb.unsubscribe(member_id)

    async def _update_icon(self):
        icon = create_tray_icon("light",
                                await self.ofb.get_state(),
                                await self.ofb.get_property("battery", "global", 0),
                                await self.ofb.get_property("anc", "mode", "normal"))
        pixmap = QIcon(ImageQt.toqpixmap(icon))
        self.setIcon(pixmap)
