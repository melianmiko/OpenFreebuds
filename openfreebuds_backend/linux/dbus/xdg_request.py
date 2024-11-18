import asyncio
import uuid
from contextlib import asynccontextmanager

from dbus_next import BusType, Variant, Message
from dbus_next.aio import ProxyObject, MessageBus


class XdgDesktopPortalRequest:
    @asynccontextmanager
    async def handle_request(self, bus_object: ProxyObject):
        unique_name = bus_object.bus.unique_name[1:].replace(".", "_")
        handle_id = uuid.uuid4().hex
        path = f"/org/freedesktop/portal/desktop/request/{unique_name}/{handle_id}"

        class State:
            result = None
            event = asyncio.Event()

        def callback(m: Message):
            if m.path == path:
                State.result = m.body
                State.event.set()

        async def waiter():
            await State.event.wait()
            return State.result

        try:
            bus_object.bus.add_message_handler(callback)
            yield handle_id, path, waiter
        finally:
            bus_object.bus.remove_message_handler(callback)
