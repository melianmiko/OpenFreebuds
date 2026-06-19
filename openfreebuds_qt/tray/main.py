import asyncio
from typing import Optional

from PIL import ImageQt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QSystemTrayIcon
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.exceptions import OfbServerDeadError
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config.main import OfbQtConfigParser
from openfreebuds_qt.generic import IOfbQtApplication
from openfreebuds_qt.generic import IOfbTrayIcon
from openfreebuds_qt.tray.menu import OfbQtTrayMenu
from openfreebuds_qt.utils import OfbCoreEvent, qt_error_handler, create_tray_icon

try:
    from openfreebuds_qt.app.widget.low_battery_overlay import LowBatteryOverlay
except ImportError:
    LowBatteryOverlay = None

log = create_logger("OfbTrayIcon")


class OfbTrayIcon(IOfbTrayIcon):
    """
    OpenFreebuds Tray icon implementation
    """

    def __init__(self, context: IOfbQtApplication):
        super().__init__(None)

        self._last_tooltip = ""

        # noinspection PyUnresolvedReferences
        self.activated.connect(self._on_click)

        self.ctx = context
        self.ofb = context.ofb
        self.config = OfbQtConfigParser.get_instance()

        self.ui_update_task: Optional[asyncio.Task] = None
        self._low_battery_overlay = None
        self._low_battery_alert_shown = {
            10: False,
            20: False,
        }
        self._low_battery_device_addr = ""
        self._battery_summary_device_addr = ""
        self._battery_summary_overlay_shown = False

        self.menu = OfbQtTrayMenu(self, self.ctx, self.ofb)
        self.setContextMenu(self.menu)

    @asyncSlot(QSystemTrayIcon.ActivationReason)
    async def _on_click(self, reason):
        if (
            reason == self.ActivationReason.Trigger
            and await self.ofb.get_state() == self.ofb.STATE_CONNECTED
        ):
            async with qt_error_handler("OfbTrayIcon_OnClick", self.ctx):
                tray_shortcut = self.config.get("ui", "tray_shortcut", "next_mode")
                await self.ofb.run_shortcut(tray_shortcut)

    async def boot(self):
        """
        Will start UI update loop and perform other preparations on boot
        """
        async with qt_error_handler("OfbTrayIcon_Boot", self.ctx):
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
            self.setToolTip(self.tr("OpenFreebuds: Connecting to device…"))
        else:
            self.setToolTip("OpenFreebuds")

        if state == IOpenFreebuds.STATE_CONNECTED:
            summary_shown = False
            if event.kind_match(OfbEventKind.STATE_CHANGED) or event.is_changed("battery", ""):
                summary_shown = await self._check_battery_summary_overlay()
            if event.is_changed("battery", "") and not summary_shown:
                await self._check_low_battery_overlay()
        else:
            self._reset_low_battery_alerts()
            self._reset_battery_summary_overlay()

        await self.menu.on_core_event(event, state)

    async def _get_tooltip_text(self, event: OfbCoreEvent):
        """
        Create tooltip text for tray icon
        """
        if event.is_changed("battery") or event.kind_match(OfbEventKind.DEVICE_CHANGED) or self._last_tooltip == "":
            device_name, _ = await self.ofb.get_device_tags()
            battery = await self.ofb.get_property("battery", "global", "--")
            self._last_tooltip = f"{device_name}: {battery}%"

        return self._last_tooltip

    async def _check_battery_summary_overlay(self):
        if not self.config.get("ui", "battery_overlay_on_connect", False):
            return False

        battery = await self.ofb.get_property("battery")
        if battery is None:
            return False

        device_name, device_addr = await self.ofb.get_device_tags()
        if device_addr != self._battery_summary_device_addr:
            self._battery_summary_device_addr = device_addr
            self._battery_summary_overlay_shown = False

        if self._battery_summary_overlay_shown:
            return False

        self._battery_summary_overlay_shown = True
        self._show_low_battery_overlay(device_name, battery, 0)
        return True

    async def _check_low_battery_overlay(self):
        if not self.config.get("ui", "low_battery_overlay", True):
            return

        battery = await self.ofb.get_property("battery")
        if battery is None:
            return

        device_name, device_addr = await self.ofb.get_device_tags()
        if device_addr != self._low_battery_device_addr:
            self._low_battery_device_addr = device_addr
            self._reset_low_battery_alerts()

        min_battery = self._get_min_battery_level(battery)
        if min_battery is None:
            return

        if min_battery > 25:
            self._low_battery_alert_shown[20] = False
        if min_battery > 15:
            self._low_battery_alert_shown[10] = False

        threshold = None
        if min_battery <= 10:
            threshold = 10
        elif min_battery <= 20:
            threshold = 20

        if threshold is None or self._low_battery_alert_shown[threshold]:
            return

        self._low_battery_alert_shown[threshold] = True
        self._show_low_battery_overlay(device_name, battery, threshold)

    def _show_low_battery_overlay(self, device_name: str, battery: dict, threshold: int):
        if LowBatteryOverlay is None:
            log.warning("Low battery overlay is not available")
            return

        try:
            if self._low_battery_overlay is not None:
                self._low_battery_overlay.close()

            overlay = LowBatteryOverlay(device_name, battery, threshold)
            overlay.destroyed.connect(lambda _=None, current=overlay: self._on_low_battery_overlay_destroyed(current))
            self._low_battery_overlay = overlay
            overlay.show_overlay()
        except Exception:
            log.exception("Failed to show low battery overlay")

    def _on_low_battery_overlay_destroyed(self, overlay):
        if self._low_battery_overlay is overlay:
            self._low_battery_overlay = None

    async def show_low_battery_overlay_preview(self):
        if await self.ofb.get_state() != IOpenFreebuds.STATE_CONNECTED:
            return

        device_name, _ = await self.ofb.get_device_tags()
        self._show_low_battery_overlay(
            device_name,
            {
                "left": 10,
                "right": 20,
                "case": 42,
            },
            10,
        )

    def _reset_low_battery_alerts(self):
        self._low_battery_alert_shown[10] = False
        self._low_battery_alert_shown[20] = False

    def _reset_battery_summary_overlay(self):
        self._battery_summary_device_addr = ""
        self._battery_summary_overlay_shown = False

    @staticmethod
    def _get_min_battery_level(battery: dict):
        levels = []
        for key in ("left", "right", "case", "global"):
            value = battery.get(key)
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                levels.append(value)
            elif isinstance(value, str) and value.isdigit():
                levels.append(int(value))

        if not levels:
            return None
        return min(levels)

    async def _update_loop(self):
        """
        Background task that will subscribe to core event bus and watch
        for changes to perform tray UI update when something changes.
        """

        async with qt_error_handler("OfbTrayIcon_EventLoop", self.ctx):
            member_id = await self.ofb.subscribe()
            log.info(f"Tray update loop started, member_id={member_id}")

            try:
                while True:
                    kind, *args = await self.ofb.wait_for_event(member_id)
                    event = OfbCoreEvent(kind, *args)

                    if event.kind_match(OfbEventKind.QT_BRING_SETTINGS_UP):
                        self.ctx.main_window.show()
                        self.ctx.main_window.activateWindow()

                    if event.kind_match(OfbEventKind.STATE_CHANGED) and args[0] == IOpenFreebuds.STATE_DESTROYED:
                        raise OfbServerDeadError("Server going to exit")

                    if event.kind_in([
                        OfbEventKind.STATE_CHANGED,
                        OfbEventKind.QT_SETTINGS_CHANGED,
                        OfbEventKind.PROPERTY_CHANGED,
                    ]):
                        await self._update_ui(event)
            except asyncio.CancelledError:
                await self.ofb.unsubscribe(member_id)
            except OfbServerDeadError:
                log.info("Server is dead, exiting now…")
                self.ui_update_task = None
                await self.ctx.exit(1)
