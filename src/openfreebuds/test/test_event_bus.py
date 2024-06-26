import asyncio

import pytest

from openfreebuds.utils.event_bus import Subscription


@pytest.mark.asyncio
async def test_event_bus_base():
    bus = Subscription()

    async def _recv():
        sub_id = await bus.subscribe()
        while True:
            async with asyncio.timeout(0.5):
                event = await bus.wait_for_event(sub_id)
                print("recv", event)

    t = asyncio.create_task(_recv())

    for i in range(4):
        await asyncio.sleep(0.25)
        print("send")
        await bus.send_message("Test", "message")

    t.cancel()
