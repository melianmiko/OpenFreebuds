import asyncio
from asyncio import Task

import openfreebuds_backend
from openfreebuds.driver.generic import FbDriverGeneric
from openfreebuds.utils.event_bus import Subscription
from openfreebuds.exceptions import FbNoDeviceError, FbDriverError
from openfreebuds.utils.logger import create_logger

log = create_logger("OpenFreebuds")


class OpenFreebuds:
    MAINLOOP_TIMEOUT = 1

    STATE_NO_DEV = 0
    STATE_OFFLINE = 1
    STATE_DISCONNECTED = 2
    STATE_WAIT = 3
    STATE_CONNECTED = 4
    STATE_FAILED = 5
    STATE_PAUSED = 6

    def __init__(self):
        self.changes = Subscription()
        self.state = OpenFreebuds.STATE_NO_DEV      # type: int
        self._driver = None                         # type: FbDriverGeneric | None
        self._task = None                           # type: Task | None
        self._paused = False

    async def start(self, driver: FbDriverGeneric):
        if self._task is not None and not self._task.done():
            await self.stop()

        self._driver = driver
        self._task = asyncio.create_task(self._mainloop())

    async def stop(self):
        self._task.cancel("stop() requested")
        await self._driver.stop()
        self._driver = None
        self._task = None

    async def get_property(self, group: str, prop: str = None, fallback=None) -> str | dict:
        return await self._driver.get_property(group, prop, fallback)

    async def set_property(self, group: str, prop: str, value: str):
        if self._driver is None:
            raise FbNoDeviceError("Attempt to write prop without device")
        await self._driver.set_property(group, prop, value)

    async def _mainloop(self):
        log.info(f"Started")

        while True:
            if not openfreebuds_backend.bt_is_connected(self._driver.device_address):
                await self._set_state(OpenFreebuds.STATE_OFFLINE)
                if self._driver.started:
                    log.info("Device disconnected from OS, stop driver...")
                    await self._driver.stop()
                await asyncio.sleep(2)
                continue

            if not self._driver.started:
                log.info("Trying bring driver up...")
                await self._set_state(OpenFreebuds.STATE_WAIT)
                try:
                    await self._driver.start()
                    await self._set_state(OpenFreebuds.STATE_CONNECTED)
                except FbDriverError:
                    await self._set_state(OpenFreebuds.STATE_FAILED)
                    await asyncio.sleep(5)
                    continue

            await asyncio.sleep(2)

    async def _use_device_driver(self, driver: FbDriverGeneric):
        if self._driver:
            await self._driver.stop()
        self._driver = driver

    async def _set_state(self, new_state: int):
        if self.state == new_state:
            return

        self.state = new_state
        await self.changes.message("STATE_CHANGED", new_state)
