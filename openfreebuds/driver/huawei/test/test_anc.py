import asyncio
from collections import deque

import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.driver.per_model.buds_pro_5 import OfbDriverHuaweiPro5
from openfreebuds.driver.huawei.handler import OfbHuaweiAncHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import OfbDriverError


class SequentialAncFixture(FbDriverHuaweiGenericFixture):
    def __init__(self, handler, responses):
        super().__init__(handlers=[handler], package_response_model={})
        self.responses = {
            request: deque(script)
            for request, script in responses.items()
        }
        self.gated_request = None
        self.request_blocked = asyncio.Event()
        self.release_request = asyncio.Event()

    def gate_next(self, request: bytes):
        self.gated_request = request
        self.request_blocked.clear()
        self.release_request.clear()

    async def _send_nowait(self, pkg: HuaweiSppPackage):
        request = pkg.to_bytes()
        self.package_log.append(("send", request))

        if request == self.gated_request:
            self.gated_request = None
            self.request_blocked.set()
            await self.release_request.wait()

        scripted = self.responses.get(request)
        if scripted:
            response = scripted.popleft()
            if response is not None:
                await self._handle_raw_pkg(response)


def anc_state(mode: int, level: int = 0) -> HuaweiSppPackage:
    return HuaweiSppPackage(
        b"\x2b\x2a",
        [(1, bytes([level, mode])), (2, b"\x05")],
    )


def verified_handler() -> OfbHuaweiAncHandler:
    return OfbHuaweiAncHandler(
        w_cancel_lvl=True,
        w_voice_boost=True,
        w_change_readback=True,
    )


def test_pro_5_enables_verified_change_readback():
    driver = OfbDriverHuaweiPro5("")
    anc_handler = next(
        handler
        for handler in driver.handlers
        if isinstance(handler, OfbHuaweiAncHandler)
    )

    assert anc_handler.w_change_readback is True


@pytest.mark.asyncio
async def test_verified_change_uses_no_wait_write_and_explicit_readback():
    handler = verified_handler()
    read_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2])
    set_awareness = HuaweiSppPackage.change_rq_nowait(b"\x2b\x04", [(1, b"\x02\xff")])
    normal = anc_state(0)
    awareness = anc_state(2, 2)
    driver = SequentialAncFixture(
        handler,
        {read_anc.to_bytes(): [normal.to_bytes(), awareness.to_bytes()]},
    )
    await driver.start()

    await driver.set_property("anc", "mode", "awareness")

    assert await driver.get_property("anc", "mode") == "awareness"
    assert driver.package_log == [
        ("send", set_awareness.to_bytes()),
        ("send", read_anc.to_bytes()),
        ("recv", awareness.to_bytes()),
    ]


@pytest.mark.asyncio
async def test_verified_change_retries_after_stale_readback():
    handler = verified_handler()
    read_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2])
    set_awareness = HuaweiSppPackage.change_rq_nowait(b"\x2b\x04", [(1, b"\x02\xff")])
    normal = anc_state(0)
    awareness = anc_state(2, 2)
    driver = SequentialAncFixture(
        handler,
        {
            read_anc.to_bytes(): [
                normal.to_bytes(),
                normal.to_bytes(),
                awareness.to_bytes(),
            ],
        },
    )
    await driver.start()

    await driver.set_property("anc", "mode", "awareness")

    assert await driver.get_property("anc", "mode") == "awareness"
    assert driver.package_log == [
        ("send", set_awareness.to_bytes()),
        ("send", read_anc.to_bytes()),
        ("recv", normal.to_bytes()),
        ("send", read_anc.to_bytes()),
        ("recv", awareness.to_bytes()),
    ]


@pytest.mark.asyncio
async def test_verified_change_writes_and_confirms_current_value():
    handler = verified_handler()
    read_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2])
    set_normal = HuaweiSppPackage.change_rq_nowait(b"\x2b\x04", [(1, b"\x00\xff")])
    normal = anc_state(0)
    driver = SequentialAncFixture(
        handler,
        {read_anc.to_bytes(): [normal.to_bytes(), normal.to_bytes()]},
    )
    await driver.start()

    await driver.set_property("anc", "mode", "normal")

    assert driver.package_log == [
        ("send", set_normal.to_bytes()),
        ("send", read_anc.to_bytes()),
        ("recv", normal.to_bytes()),
    ]


@pytest.mark.asyncio
async def test_verified_changes_are_serialized():
    handler = verified_handler()
    read_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2])
    set_normal = HuaweiSppPackage.change_rq_nowait(b"\x2b\x04", [(1, b"\x00\xff")])
    set_awareness = HuaweiSppPackage.change_rq_nowait(b"\x2b\x04", [(1, b"\x02\xff")])
    set_cancellation = HuaweiSppPackage.change_rq_nowait(b"\x2b\x04", [(1, b"\x01\xff")])
    normal = anc_state(0)
    awareness = anc_state(2, 2)
    cancellation = anc_state(1)
    driver = SequentialAncFixture(
        handler,
        {
            read_anc.to_bytes(): [
                normal.to_bytes(),
                normal.to_bytes(),
                awareness.to_bytes(),
                cancellation.to_bytes(),
            ],
        },
    )
    await driver.start()

    driver.gate_next(read_anc.to_bytes())
    normal_task = asyncio.create_task(driver.set_property("anc", "mode", "normal"))
    await driver.request_blocked.wait()

    awareness_task = asyncio.create_task(driver.set_property("anc", "mode", "awareness"))
    cancellation_task = asyncio.create_task(driver.set_property("anc", "mode", "cancellation"))
    await asyncio.sleep(0)

    assert driver.package_log == [
        ("send", set_normal.to_bytes()),
        ("send", read_anc.to_bytes()),
    ]

    driver.release_request.set()
    await asyncio.gather(normal_task, awareness_task, cancellation_task)

    assert await driver.get_property("anc", "mode") == "cancellation"
    assert driver.package_log == [
        ("send", set_normal.to_bytes()),
        ("send", read_anc.to_bytes()),
        ("recv", normal.to_bytes()),
        ("send", set_awareness.to_bytes()),
        ("send", read_anc.to_bytes()),
        ("recv", awareness.to_bytes()),
        ("send", set_cancellation.to_bytes()),
        ("send", read_anc.to_bytes()),
        ("recv", cancellation.to_bytes()),
    ]


@pytest.mark.asyncio
async def test_verified_change_retries_after_readback_timeout():
    handler = verified_handler()
    handler.change_readback_attempts = 2
    handler.change_readback_timeout = 0.01
    read_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2])
    normal = anc_state(0)
    awareness = anc_state(2, 2)
    driver = SequentialAncFixture(
        handler,
        {
            read_anc.to_bytes(): [
                normal.to_bytes(),
                None,
                awareness.to_bytes(),
            ],
        },
    )
    await driver.start()

    await driver.set_property("anc", "mode", "awareness")
    assert await driver.get_property("anc", "mode") == "awareness"


@pytest.mark.asyncio
async def test_verified_change_restores_cached_mode_after_exhausted_readbacks():
    handler = verified_handler()
    handler.change_readback_attempts = 1
    handler.change_readback_timeout = 0.01
    read_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2])
    normal = anc_state(0)
    driver = SequentialAncFixture(
        handler,
        {
            read_anc.to_bytes(): [
                normal.to_bytes(),
                None,
                normal.to_bytes(),
            ],
        },
    )
    await driver.start()

    with pytest.raises(OfbDriverError):
        await driver.set_property("anc", "mode", "awareness")

    await driver.set_property("anc", "mode", "normal")
    assert await driver.get_property("anc", "mode") == "normal"

    sent_changes = []
    for direction, package in driver.package_log:
        if direction != "send":
            continue
        parsed = HuaweiSppPackage.from_bytes(package)
        if parsed.command_id == b"\x2b\x04":
            sent_changes.append(parsed.find_param(1))
    assert sent_changes == [b"\x02\xff", b"\x00\xff"]


@pytest.mark.asyncio
async def test_verified_level_change_confirms_mode_and_level():
    handler = verified_handler()
    read_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2])
    set_ultra = HuaweiSppPackage.change_rq_nowait(b"\x2b\x04", [(1, b"\x01\x02")])
    cancellation_normal = anc_state(1, 0)
    cancellation_ultra = anc_state(1, 2)
    driver = SequentialAncFixture(
        handler,
        {
            read_anc.to_bytes(): [
                cancellation_normal.to_bytes(),
                cancellation_ultra.to_bytes(),
            ],
        },
    )
    await driver.start()

    await driver.set_property("anc", "level", "ultra")

    assert await driver.get_property("anc", "level") == "ultra"
    assert driver.package_log[0] == ("send", set_ultra.to_bytes())


@pytest.mark.asyncio
async def test_default_change_still_waits_for_ack_then_reads_state():
    handler = OfbHuaweiAncHandler(w_cancel_lvl=True, w_voice_boost=True)
    read_anc = HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2])
    set_awareness = HuaweiSppPackage.change_rq(b"\x2b\x04", [(1, b"\x02\xff")])
    ack = HuaweiSppPackage(b"\x2b\x04", [(0x7f, b"\x00")])
    normal = anc_state(0)
    awareness = anc_state(2, 2)
    driver = FbDriverHuaweiGenericFixture(
        handlers=[handler],
        package_response_model={
            read_anc.to_bytes(): [normal.to_bytes()],
            set_awareness.to_bytes(): [ack.to_bytes()],
        },
    )
    await driver.start()
    driver.package_response_model[read_anc.to_bytes()] = [awareness.to_bytes()]

    await driver.set_property("anc", "mode", "awareness")

    assert await driver.get_property("anc", "mode") == "awareness"
    assert driver.package_log == [
        ("send", set_awareness.to_bytes()),
        ("recv", ack.to_bytes()),
        ("send", read_anc.to_bytes()),
        ("recv", awareness.to_bytes()),
    ]
