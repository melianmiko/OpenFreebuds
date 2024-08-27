import asyncio
from typing import Optional

from PIL import ImageQt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QSystemTrayIcon
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.exceptions import FbServerDeadError
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.config.main import OfbQtConfigParser
from openfreebuds_qt.generic import IOfbQtMainWindow
from openfreebuds_qt.tray.generic import IOfbTrayIcon
from openfreebuds_qt.icon import create_tray_icon
from openfreebuds_qt.tray.menu import OfbQtTrayMenu

UI_UPDATE_GROUPS = ["anc", "battery"]
log = create_logger("OfbTrayIcon")


class OfbTrayIcon(IOfbTrayIcon):
    """
    OpenFreebuds Tray icon implementation
    """

    def __init__(self, root: IOfbQtMainWindow):
        super().__init__(root)

        self._last_tooltip = ""

        # noinspection PyUnresolvedReferences
        self.activated.connect(self._on_click)

        self.root = root
        self.ofb = root.ofb
        self.config = OfbQtConfigParser.get_instance()

        self.ui_update_task: Optional[asyncio.Task] = None

        self.menu = OfbQtTrayMenu(self, self.root, self.ofb)
        self.setContextMenu(self.menu)

    @asyncSlot(QSystemTrayIcon.ActivationReason)
    async def _on_click(self, reason):
        if (
            reason == self.ActivationReason.Trigger
            and await self.ofb.get_state() == self.ofb.STATE_CONNECTED
        ):
            await self.ofb.run_shortcut(self.config.get("ui", "tray_shortcut", "anc_next"))

    async def boot(self):
        """
        Will start UI update loop and perform other preparations on boot
        """
        if self.ui_update_task is None:
            self.ui_update_task = asyncio.create_task(self._update_loop())

        await self._update_ui(OfbCoreEvent(None))

    async def close(self):
        """
        Will stop UI update loop
        """
        if self.ui_update_task is not None:
            self.ui_update_task.cancel()
            await self.ui_update_task
            self.ui_update_task = None

    async def _update_ui(self, event: OfbCoreEvent):
        """
        UI update callback
        """

        state = await self.ofb.get_state()

        # Update icon
        icon = create_tray_icon(self.config.get_tray_icon_theme(),
                                state,
                                await self.ofb.get_property("battery", "global", 0),
                                await self.ofb.get_property("anc", "mode", "normal"))
        pixmap = QIcon(ImageQt.toqpixmap(icon))
        self.setIcon(pixmap)

        # Update menu and tooltip
        if state == IOpenFreebuds.STATE_CONNECTED:
            self.setToolTip(await self._get_tooltip_text(event))
        elif state == IOpenFreebuds.STATE_WAIT:
            self.setToolTip(self.tr("OpenFreebuds: Connecting to device..."))
        else:
            self.setToolTip("OpenFreebuds")

        await self.menu.on_core_event(event)

    async def _get_tooltip_text(self, event: OfbCoreEvent):
        """
        Create tooltip text for tray icon
        """
        if event.is_changed("battery") or event.kind_match(OfbEventKind.DEVICE_CHANGED) or self._last_tooltip == "":
            device_name, _ = await self.ofb.get_device_tags()
            battery = await self.ofb.get_property("battery", "global", "--")
            self._last_tooltip = f"{device_name}: {battery}%"

        return self._last_tooltip

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
                if kind == OfbEventKind.QT_BRING_SETTINGS_UP:
                    self.root.show()
                    self.root.activateWindow()
                if kind == OfbEventKind.STATE_CHANGED and args[0] == IOpenFreebuds.STATE_DESTROYED:
                    raise FbServerDeadError("Server going to exit")
                if kind == OfbEventKind.STATE_CHANGED or (kind == OfbEventKind.PROPERTY_CHANGED and args[0] in UI_UPDATE_GROUPS):
                    await self._update_ui(OfbCoreEvent(kind, *args))
        except asyncio.CancelledError:
            await self.ofb.unsubscribe(member_id)
        except FbServerDeadError:
            log.info("Server is dead, exiting now...")
            self.ui_update_task = None
            await self.root.exit(1)
