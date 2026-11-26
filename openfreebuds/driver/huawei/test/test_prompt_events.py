"""0x2B7F prompt-event parsing and mounting tests.

Frames are the official TLV values derived from general_prompt_config.json.
The captured IConnect data is assumed to arrive over SPP unchanged.
"""

import pytest

from openfreebuds import OfbEventKind
from openfreebuds.driver.huawei.constants import CMD_PROMPT_EVENT
from openfreebuds.driver.huawei.driver.per_model.buds_6 import OfbDriverHuawei6
from openfreebuds.driver.huawei.driver.per_model.buds_7 import OfbDriverHuawei7
from openfreebuds.driver.huawei.driver.per_model.buds_neo import OfbDriverHuaweiNeo
from openfreebuds.driver.huawei.driver.per_model.free_clip import OfbDriverHuaweiFreeClip
from openfreebuds.driver.huawei.driver.per_model.free_clip_2 import OfbDriverHuaweiFreeClip2
from openfreebuds.driver.huawei.driver.per_model.free_clip_2_s import OfbDriverHuaweiFreeClip2S
from openfreebuds.driver.huawei.handler.prompt_events import (
    PROMPT_EVENT_CLEANING,
    PROMPT_EVENT_CLEANING_CANCEL,
    PROMPT_EVENT_CLEANING_MISPLACE,
    PROMPT_EVENT_DROP,
    OfbHuaweiPromptEventsHandler,
    parse_prompt_event,
)
from openfreebuds.driver.huawei.package import HuaweiSppPackage


def _pkg(param: int, value: int | bytes) -> HuaweiSppPackage:
    return HuaweiSppPackage.change_rq(CMD_PROMPT_EVENT, [(param, value)])


def test_parse_cleaning_event():
    assert parse_prompt_event(_pkg(2, 1)) == PROMPT_EVENT_CLEANING


def test_parse_drop_event():
    assert parse_prompt_event(_pkg(5, 1)) == PROMPT_EVENT_DROP


def test_parse_cleaning_cancel():
    assert parse_prompt_event(_pkg(6, 20)) == PROMPT_EVENT_CLEANING_CANCEL


def test_parse_cleaning_misplace():
    assert parse_prompt_event(_pkg(6, 21)) == PROMPT_EVENT_CLEANING_MISPLACE


def test_ignore_status_packet():
    assert parse_prompt_event(_pkg(6, b"\x02\x00")) is None


def test_ignore_other_command_and_unknown_value():
    assert parse_prompt_event(HuaweiSppPackage.change_rq(b"\x2b\x7e", [(2, 1)])) is None
    assert parse_prompt_event(_pkg(2, 0)) is None


class _FakeChanges:
    def __init__(self):
        self.messages = []

    async def send_message(self, kind, *args):
        self.messages.append((kind, *args))


class _FakeDriver:
    def __init__(self):
        self.changes = _FakeChanges()


@pytest.mark.asyncio
async def test_handler_emits_prompt_event():
    handler = OfbHuaweiPromptEventsHandler(w_cleaning=True)
    handler.driver = _FakeDriver()
    await handler.on_package(_pkg(5, 1))

    assert handler.driver.changes.messages == [
        (OfbEventKind.HUAWEI_PROMPT_EVENT, PROMPT_EVENT_DROP)
    ]


@pytest.mark.asyncio
async def test_drop_only_handler_ignores_cleaning():
    handler = OfbHuaweiPromptEventsHandler(w_cleaning=False)
    handler.driver = _FakeDriver()
    await handler.on_package(_pkg(2, 1))

    assert handler.driver.changes.messages == []


@pytest.mark.parametrize("driver_cls", [
    OfbDriverHuaweiFreeClip,
    OfbDriverHuaweiFreeClip2,
    OfbDriverHuaweiFreeClip2S,
    OfbDriverHuawei6,
    OfbDriverHuawei7,
    OfbDriverHuaweiNeo,
])
def test_prompt_event_handler_is_mounted(driver_cls):
    driver = driver_cls("00:11:22:33:44:55")
    handlers = [h for h in driver.handlers if isinstance(h, OfbHuaweiPromptEventsHandler)]
    assert len(handlers) == 1


@pytest.mark.parametrize(("driver_cls", "w_cleaning"), [
    (OfbDriverHuaweiFreeClip, True),
    (OfbDriverHuaweiFreeClip2, True),
    (OfbDriverHuaweiFreeClip2S, True),
    (OfbDriverHuawei6, False),
    (OfbDriverHuawei7, False),
    (OfbDriverHuaweiNeo, False),
])
def test_prompt_event_cleaning_scope(driver_cls, w_cleaning):
    driver = driver_cls("00:11:22:33:44:55")
    handler = next(h for h in driver.handlers if isinstance(h, OfbHuaweiPromptEventsHandler))
    assert handler.w_cleaning is w_cleaning
