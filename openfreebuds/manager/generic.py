from contextlib import asynccontextmanager

from openfreebuds.utils.event_bus import Subscription


class IOpenFreebuds(Subscription):
    STATE_DESTROYED = -1
    STATE_STOPPED = 0
    STATE_DISCONNECTED = 1
    STATE_WAIT = 2
    STATE_CONNECTED = 3
    STATE_FAILED = 4
    STATE_PAUSED = 5

    async def get_state(self) -> int:
        raise NotImplementedError("Not implemented")

    async def get_logs(self) -> str:
        raise NotImplementedError("Not implemented")

    async def start(self, device_name: str, device_address: str):
        raise NotImplementedError("Not implemented")

    async def get_health_report(self):
        raise NotImplementedError("Not implemented")

    async def destroy(self):
        raise NotImplementedError("Not implemented")

    async def stop(self):
        raise NotImplementedError("Not implemented")

    async def get_device_tags(self):
        raise NotImplementedError("Not implemented")

    async def get_property(self, group: str = None, prop: str = None, fallback=None):
        raise NotImplementedError("Not implemented")

    async def set_property(self, group: str, prop: str, value: str):
        raise NotImplementedError("Not implemented")

    async def run_shortcut(self, *args, no_catch: bool = False):
        raise NotImplementedError("Not implemented")

    async def request_property_update(self, handler_id: str):
        raise NotImplementedError("Not implemented")

    @asynccontextmanager
    async def locked_device(self):
        raise NotImplementedError("Not implemented")
