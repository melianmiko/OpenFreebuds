from typing import Optional

from openfreebuds.constants import OfbEventKind
from openfreebuds.exceptions import FbMissingHandlerError
from openfreebuds.utils.event_bus import Subscription
from openfreebuds.utils.logger import create_logger
from openfreebuds_backend import bt_is_connected

log = create_logger("OfbDriverGeneric")


class OfbDriverHandlerGeneric:
    properties: list[tuple[str, str]] = []

    async def set_property(self, group: str, prop: str, value: str):
        raise NotImplementedError()


class OfbDriverGeneric:
    def __init__(self, address: str):
        self.__set_prop_handlers: dict[str, OfbDriverHandlerGeneric] = {}

        self._store: dict[str, dict[str, str]] = {}

        self.device_address: str = address
        self.started: bool = False
        self.changes = Subscription()

    async def is_device_online(self):
        return await bt_is_connected(self.device_address)

    async def start(self):
        raise NotImplementedError()

    async def stop(self):
        self.__set_prop_handlers = {}

    async def get_health_report(self):
        return {
            "started": self.started,
            "address": self.device_address,
            "store_content": self._store,
            "available_store_handlers": list(self.__set_prop_handlers.keys())
        }

    def healthy(self):
        return self.started

    def _add_set_property_handler(self, handler: OfbDriverHandlerGeneric):
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

    async def put_property(
            self,
            group: Optional[str],
            prop: Optional[str],
            value: Optional[str | dict],
            extend_group: bool = False,
    ):
        if group is None:
            log.info("Reassigned entire store, this should happen only in debug drviers")
            self._store = value
        elif prop is None and extend_group:
            data = {**self._store.get(group, {}), **value}
            self._store[group] = data
        elif prop is None:
            self._store[group] = value
        else:
            if group not in self._store:
                self._store[group] = {}

            self._store[group][prop] = value

        await self.changes.send_message(OfbEventKind.PROPERTY_CHANGED, group, prop, value)

    async def request_property_update(self, handler_id: str):
        """Request a property update from a specific handler"""
        raise NotImplementedError()
