"""System notification routing tests for HUAWEI prompt events."""

from types import SimpleNamespace

import pytest
from PyQt6.QtCore import QCoreApplication

from openfreebuds.driver.huawei.handler.prompt_events import (
    PROMPT_EVENT_CLEANING,
    PROMPT_EVENT_CLEANING_CANCEL,
    PROMPT_EVENT_CLEANING_MISPLACE,
    PROMPT_EVENT_DROP,
)
from openfreebuds_qt.utils.notifications import (
    HIGH,
    NORMAL,
    OfbLinuxNotificationBackend,
    OfbQtSystemNotificationService,
    OfbSystemNotificationBackend,
)


class _FakeOfb:
    async def get_device_tags(self):
        return "HUAWEI FreeClip 2", "02:00:00:00:00:01"


class _FakeBackend(OfbSystemNotificationBackend):
    def __init__(self):
        self.shown = []
        self.cancelled = 0

    async def show(self, title, body, priority, key=None):
        self.shown.append((title, body, priority, key))

    async def cancel_cleaning(self):
        self.cancelled += 1


def _qapp():
    return QCoreApplication.instance() or QCoreApplication([])


def _service():
    _qapp()
    backend = _FakeBackend()
    ctx = SimpleNamespace(ofb=_FakeOfb(), tray=None)
    return OfbQtSystemNotificationService(ctx, backend=backend), backend


@pytest.mark.asyncio
async def test_drop_event_uses_high_priority():
    service, backend = _service()
    await service.handle_event(PROMPT_EVENT_DROP)

    assert len(backend.shown) == 1
    title, body, priority, key = backend.shown[0]
    assert title == "Drop reminder"
    assert "HUAWEI FreeClip 2" in body
    assert priority == HIGH
    assert key == PROMPT_EVENT_DROP


@pytest.mark.asyncio
async def test_cleaning_events_use_normal_priority():
    service, backend = _service()
    await service.handle_event(PROMPT_EVENT_CLEANING)
    await service.handle_event(PROMPT_EVENT_CLEANING_MISPLACE)

    assert backend.shown[0][2] == NORMAL
    assert backend.shown[0][0] == "Cleaning reminder"
    assert "charging case" in backend.shown[0][1]
    assert backend.shown[1][2] == NORMAL
    assert "not seated correctly" in backend.shown[1][1]


@pytest.mark.asyncio
async def test_cleaning_cancel_does_not_show_another_popup():
    service, backend = _service()
    await service.handle_event(PROMPT_EVENT_CLEANING_CANCEL)

    assert backend.shown == []
    assert backend.cancelled == 1


@pytest.mark.asyncio
async def test_unknown_event_is_ignored():
    service, backend = _service()
    await service.handle_event("unknown")

    assert backend.shown == []
    assert backend.cancelled == 0


class _FakeDBusInterface:
    def __init__(self):
        self.notifications = []
        self.closed = []
        self.next_id = 1

    async def call_notify(self, app, replaces_id, icon, title, body, actions, hints, timeout):
        notification_id = self.next_id
        self.next_id += 1
        self.notifications.append((replaces_id, title, hints, timeout))
        return notification_id

    async def call_close_notification(self, notification_id):
        self.closed.append(notification_id)


@pytest.mark.asyncio
async def test_linux_backend_reuses_cleaning_id_and_closes_it():
    backend = OfbLinuxNotificationBackend()
    backend._interface = _FakeDBusInterface()

    await backend.show("清洁提醒", "正文", NORMAL, PROMPT_EVENT_CLEANING)
    await backend.show("清洁提醒", "正文", NORMAL, PROMPT_EVENT_CLEANING_MISPLACE)
    await backend.cancel_cleaning()

    first, second = backend._interface.notifications
    assert first[0] == 0
    assert second[0] == 1
    assert first[2]["urgency"].value == 1
    assert backend._interface.closed == [2]


@pytest.mark.asyncio
async def test_linux_backend_drop_is_high_and_not_reused():
    backend = OfbLinuxNotificationBackend()
    backend._interface = _FakeDBusInterface()

    await backend.show("掉落", "正文", HIGH, PROMPT_EVENT_DROP)

    replaces_id, title, hints, timeout = backend._interface.notifications[0]
    assert replaces_id == 0
    assert hints["urgency"].value == 2
    assert timeout == -1
    assert backend._cleaning_id is None
