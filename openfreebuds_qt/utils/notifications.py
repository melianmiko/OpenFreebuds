"""Cross-platform system notifications for HUAWEI prompt events.

The preferred backend is the freedesktop notification service on Linux because
it supports an explicit urgency hint.  Windows and macOS use Qt's system-tray
notification API; on Windows the high-priority event is shown with the critical
message icon, which is the only priority hint Qt exposes there.
"""

import asyncio
import sys
from contextlib import suppress
from typing import Optional

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QSystemTrayIcon

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.driver.huawei.handler.prompt_events import (
    PROMPT_EVENT_CLEANING,
    PROMPT_EVENT_CLEANING_CANCEL,
    PROMPT_EVENT_CLEANING_MISPLACE,
    PROMPT_EVENT_DROP,
)
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbQtSystemNotifications")

HIGH = "high"
NORMAL = "normal"


class OfbSystemNotificationBackend:
    async def start(self) -> bool:
        return True

    async def stop(self):
        pass

    async def show(self, title: str, body: str, priority: str, key: Optional[str] = None):
        raise NotImplementedError()

    async def cancel_cleaning(self):
        pass


class OfbQtTrayNotificationBackend(OfbSystemNotificationBackend):
    """Qt system-tray notification backend.

    Qt exposes no notification id or close API here, so cancel_cleaning is a
    no-op.  The cleaning notification already has a short timeout, and a later
    cancel event must not produce another popup.
    """

    def __init__(self, tray: Optional[QSystemTrayIcon]):
        self.tray = tray

    async def show(self, title: str, body: str, priority: str, key: Optional[str] = None):
        if self.tray is None:
            log.warning("No system tray, cannot show notification")
            return

        icon = (
            QSystemTrayIcon.MessageIcon.Critical
            if priority == HIGH
            else QSystemTrayIcon.MessageIcon.Information
        )
        timeout_ms = 15000 if priority == HIGH else 6000
        self.tray.showMessage(title, body, icon, timeout_ms)


class OfbLinuxNotificationBackend(OfbSystemNotificationBackend):
    """freedesktop Notifications backend with an urgency hint."""

    def __init__(self):
        self._bus = None
        self._interface = None
        self._cleaning_id: Optional[int] = None

    async def start(self) -> bool:
        try:
            from dbus_next import BusType
            from dbus_next.aio import MessageBus

            bus = await MessageBus(bus_type=BusType.SESSION).connect()
            introspection = await bus.introspect(
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
            )
            obj = bus.get_proxy_object(
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
                introspection,
            )
            self._interface = obj.get_interface("org.freedesktop.Notifications")
            self._bus = bus
            return True
        except Exception:
            log.warning("freedesktop notification service is unavailable, falling back to Qt tray")
            return False

    async def stop(self):
        if self._bus is not None:
            self._bus.disconnect()
            self._bus = None
            self._interface = None

    async def show(self, title: str, body: str, priority: str, key: Optional[str] = None):
        if self._interface is None:
            raise RuntimeError("freedesktop notification service is not connected")

        from dbus_next import Variant

        hints = {
            "urgency": Variant("y", 2 if priority == HIGH else 1),
            "desktop-entry": Variant("s", "pw.mmk.OpenFreebuds"),
        }
        cleaning = key in (PROMPT_EVENT_CLEANING, PROMPT_EVENT_CLEANING_MISPLACE)
        replaces_id = (self._cleaning_id or 0) if cleaning else 0
        notification_id = await self._interface.call_notify(
            "OpenFreebuds",
            replaces_id,
            "",
            title,
            body,
            [],
            hints,
            -1 if priority == HIGH else 6000,
        )

        if cleaning:
            self._cleaning_id = int(notification_id)

    async def cancel_cleaning(self):
        if self._interface is None or self._cleaning_id is None:
            return
        try:
            await self._interface.call_close_notification(self._cleaning_id)
        finally:
            self._cleaning_id = None


class OfbQtSystemNotificationService(QObject):
    """Subscribe to core prompt events and forward them to the OS."""

    def __init__(self, ctx, backend: Optional[OfbSystemNotificationBackend] = None):
        super().__init__()
        self.ctx = ctx
        self.ofb: IOpenFreebuds = ctx.ofb
        self._qt_backend = OfbQtTrayNotificationBackend(getattr(ctx, "tray", None))
        self._backend = backend
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._backend is None:
            self._backend = self._qt_backend
            if sys.platform == "linux":
                linux = OfbLinuxNotificationBackend()
                if await linux.start():
                    self._backend = linux

        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self):
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._backend is not None:
            await self._backend.stop()

    async def _loop(self):
        member_id = await self.ofb.subscribe()
        try:
            while True:
                kind, *args = await self.ofb.wait_for_event(member_id)
                if kind == OfbEventKind.HUAWEI_PROMPT_EVENT and args:
                    await self.handle_event(args[0])
        finally:
            await self.ofb.unsubscribe(member_id)

    async def _show(self, title: str, body: str, priority: str, key: str):
        backend = self._backend or self._qt_backend
        try:
            await backend.show(title, body, priority, key)
        except Exception:
            if backend is not self._qt_backend:
                log.exception("Native notification failed, falling back to Qt tray")
                self._backend = self._qt_backend
                await self._qt_backend.show(title, body, priority, key)
            else:
                log.exception("Failed to show system notification")

    async def handle_event(self, event: str):
        if event == PROMPT_EVENT_CLEANING_CANCEL:
            backend = self._backend or self._qt_backend
            try:
                await backend.cancel_cleaning()
            except Exception:
                log.exception("Failed to cancel cleaning notification")
            return

        if event not in (PROMPT_EVENT_DROP, PROMPT_EVENT_CLEANING, PROMPT_EVENT_CLEANING_MISPLACE):
            return

        device_name, _ = await self.ofb.get_device_tags()
        device_name = device_name or "HUAWEI"

        if event == PROMPT_EVENT_DROP:
            title = self.tr("Drop reminder")
            body = self.tr(
                "Your {0} earbuds may have fallen. Please check whether they are lost."
            ).format(device_name)
            await self._show(title, body, HIGH, event)
        elif event == PROMPT_EVENT_CLEANING:
            title = self.tr("Cleaning reminder")
            body = self.tr(
                "The charging contacts of your {0} may be dirty. "
                "Please clean the charging case and the earbud contacts."
            ).format(device_name)
            await self._show(title, body, NORMAL, event)
        else:
            title = self.tr("Cleaning reminder")
            body = self.tr(
                "The charging contacts of your {0} may be dirty, or an earbud is not seated correctly. "
                "Please clean the contacts and align the earbuds with the charging case slots."
            ).format(device_name)
            await self._show(title, body, NORMAL, event)
