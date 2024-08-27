import json

from openfreebuds.constants import OfbEventKind
from openfreebuds.exceptions import FbMissingHandlerError
from openfreebuds.utils.event_bus import Subscription
from openfreebuds.utils.logger import create_logger

log = create_logger("FbDriverGeneric")


class FbDriverHandlerGeneric:
    properties: list[tuple[str, str]] = []

    async def set_property(self, group: str, prop: str, value: str):
        raise NotImplementedError()


class FbDriverGeneric:
    def __init__(self, address: str):
        self.__set_prop_handlers: dict[str, FbDriverHandlerGeneric] = {}

        self._store: dict[str, dict[str, str]] = {}

        self.device_address: str = address
        self.started: bool = False
        self.changes = Subscription()

    async def start(self):
        raise NotImplementedError()

    async def stop(self):
        self.__set_prop_handlers = {}

    def _add_set_property_handler(self, handler: FbDriverHandlerGeneric):
        for group, prop in handler.properties:
            target_handler_id = f"{group}//{prop}"
            if target_handler_id in self.__set_prop_handlers:
                log.warning(f"Duplicate handler for {target_handler_id}")
            self.__set_prop_handlers[target_handler_id] = handler

    async def set_property(self, group: str, prop: str, value: str):
        target_handler_id = f"{group}//{prop}"
        if target_handler_id in self.__set_prop_handlers:
            return await self.__set_prop_handlers[target_handler_id].set_property(group, prop, value)

        group_handler_id = f"{group}//"
        if group_handler_id in self.__set_prop_handlers:
            return await self.__set_prop_handlers[group_handler_id].set_property(group, prop, value)

        raise FbMissingHandlerError(f"No handler for {target_handler_id}")

    async def get_property(self, group: str | None, prop: str | None, fallback: str | None = None) -> str | dict:
        if group is None:
            return self._store
        if group not in self._store:
            return fallback
        group_data = self._store[group]     # type: dict

        if prop is None:
            return group_data
        elif prop not in group_data:
            return fallback

        return group_data[prop]

    async def put_property(self, group: str, prop: str | None, value: str | dict):
        if prop is None:
            self._store[group] = value
        else:
            if group not in self._store:
                self._store[group] = {}
            if not isinstance(value, str):
                value = json.dumps(value)
            self._store[group][prop] = value

        await self.changes.send_message(OfbEventKind.PROPERTY_CHANGED, group, prop, value)
