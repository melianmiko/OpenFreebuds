from openfreebuds.exceptions import FbMissingHandlerError
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
        if target_handler_id not in self.__set_prop_handlers:
            raise FbMissingHandlerError(f"No handler for {target_handler_id}")

        return await self.__set_prop_handlers[target_handler_id].set_property(group, prop, value)

    async def get_property(self, group: str, prop: str, fallback: str) -> str | dict:
        if group not in self._store:
            return fallback
        group_data = self._store[group]     # type: dict

        if prop is None:
            return group_data
        elif prop not in group_data:
            return fallback

        return group_data[prop]

    def put_property(self, group: str, prop: str | None, value: str | dict):
        if prop is None:
            self._store[group] = value
        else:
            if group not in self._store:
                self._store[group] = {}
            self._store[group][prop] = value
