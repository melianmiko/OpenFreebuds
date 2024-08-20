import asyncio
from asyncio import Task

import openfreebuds_backend
from openfreebuds.driver import DEVICE_TO_DRIVER_MAP
from openfreebuds.driver.generic import FbDriverGeneric
from openfreebuds.utils.event_bus import Subscription
from openfreebuds.exceptions import FbNoDeviceError, FbDriverError, FbNotSupportedError
from openfreebuds.utils.logger import create_logger
from openfreebuds.utils.stupid_rpc import rpc

log = create_logger("OpenFreebuds")


class OpenFreebuds(Subscription):
    MAINLOOP_TIMEOUT = 1

    STATE_STOPPED = 0
    STATE_DISCONNECTED = 1
    STATE_WAIT = 2
    STATE_CONNECTED = 3
    STATE_FAILED = 4
    STATE_PAUSED = 5

    def __init__(self):
        super().__init__()
        self._driver = None                         # type: FbDriverGeneric | None
        self._task = None                           # type: Task | None
        self._paused = False

        self._state = OpenFreebuds.STATE_STOPPED      # type: int
        self.role: str = "standalone"
        self.server_task: Task | None = None

    @rpc
    async def get_state(self) -> int:
        return self._state

    @rpc
    async def start(self, device_name: str, device_address: str):
        if self._task is not None and not self._task.done():
            await self.stop()
        if device_name not in DEVICE_TO_DRIVER_MAP:
            raise FbNotSupportedError(f"Unknown device {device_name}")

        self._driver = DEVICE_TO_DRIVER_MAP[device_name](device_address)
        self.include_subscription("inner_driver", self._driver.changes)
        self._task = asyncio.create_task(self._mainloop())

    @rpc
    async def stop(self):
        if self._task is not None:
            self._task.cancel("stop() requested")
        if self.server_task is not None:
            self.server_task.cancel("stop() requested")
        if self._driver is not None:
            await self._driver.stop()

        await self._set_state(OpenFreebuds.STATE_STOPPED)
        self._driver = None
        self._task = None

    @rpc
    async def get_property(self, group: str = None, prop: str = None, fallback=None):
        if not self._driver:
            return fallback
        return await self._driver.get_property(group, prop, fallback)

    @rpc
    async def set_property(self, group: str, prop: str, value: str):
        if self._driver is None:
            raise FbNoDeviceError("Attempt to write prop without device")
        await self._driver.set_property(group, prop, value)

    async def _mainloop(self):
        log.info(f"Started")

        while True:
            if not openfreebuds_backend.bt_is_connected(self._driver.device_address):
                await self._set_state(OpenFreebuds.STATE_DISCONNECTED)
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
        if self._state == new_state:
            return

        self._state = new_state
        await self.send_message("state_changed", new_state)
