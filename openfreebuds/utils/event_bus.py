import asyncio
from asyncio import Queue, Task
from uuid import uuid4

from openfreebuds.utils.logger import create_logger
from openfreebuds.utils.stupid_rpc import rpc

log = create_logger("EventBus")


class Subscription:
    def __init__(self):
        self._callbacks: dict[str, tuple[list[str] | None, Queue]] = {}
        self._child_subs: dict[str, Task] = {}
        self.role: str = "standalone"

    @rpc
    async def send_message(self, kind, *args):
        for kind_filters, queue in self._callbacks.values():
            if kind_filters is not None and kind not in kind_filters:
                continue
            await queue.put((kind, *args))

    def include_subscription(self, callback_id: str, subscription):
        # Include another subscription into them, transfer their messages into us
        if callback_id in self._child_subs:
            self._child_subs[callback_id].cancel()

        async def _handler():
            # noinspection PyProtectedMember
            queue = subscription._new_queue(callback_id, None)
            while True:
                await self.send_message(*(await queue.get()))

        t = asyncio.create_task(_handler())
        self._child_subs[callback_id] = t

    def _new_queue(self, member_id, kind_filters):
        q = Queue()
        self._callbacks[member_id] = (kind_filters, q)
        return q

    @rpc
    async def subscribe(
            self,
            member_id: str = None,
            kind_filters: list[str] | None = None,
    ) -> str:
        if member_id is None:
            member_id = str(uuid4())

        self._new_queue(member_id, kind_filters)
        log.info(f"Add subscriber {member_id}")
        return member_id

    @rpc
    async def wait_for_event(self, member_id: str):
        return await self._callbacks[member_id][1].get()

    @rpc
    async def unsubscribe(self, member_id: str):
        log.info(f"Leave subscriber {member_id}")
        del self._callbacks[member_id]
