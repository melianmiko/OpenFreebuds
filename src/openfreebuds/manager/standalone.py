import asyncio
from asyncio import Task
from contextlib import asynccontextmanager

import openfreebuds_backend
from openfreebuds.driver import DEVICE_TO_DRIVER_MAP
from openfreebuds.driver.generic import FbDriverGeneric
from openfreebuds.exceptions import FbNoDeviceError, FbDriverError, FbNotSupportedError
from openfreebuds.manager.generic import IOpenFreebuds
from openfreebuds.shortcuts import OpenFreebudsShortcuts
from openfreebuds.utils.logger import create_logger
from openfreebuds.utils.stupid_rpc import rpc

log = create_logger("OpenFreebuds")


class OpenFreebuds(IOpenFreebuds):
    def __init__(self):
        super().__init__()
        self._driver = None  # type: FbDriverGeneric | None
        self._task = None  # type: Task | None
        self._device_tags = "", ""  # type: tuple[str, str]
        self._paused = False
        self._shortcuts = OpenFreebudsShortcuts(self)

        self._state = OpenFreebuds.STATE_STOPPED  # type: int
        self.role: str = "standalone"
        self.server_task: Task | None = None

    @rpc
    async def get_state(self) -> int:
        return self._state

    @rpc
    async def start(self, device_name: str, device_address: str):
        await self.stop()
        if device_name not in DEVICE_TO_DRIVER_MAP:
            raise FbNotSupportedError(f"Unknown device {device_name}")

        self._driver = DEVICE_TO_DRIVER_MAP[device_name](device_address)
        self.include_subscription("inner_driver", self._driver.changes)
        self._task = asyncio.create_task(self._mainloop())
        self._device_tags = device_name, device_address
        await self.send_message("device_changed")

    @rpc
    async def destroy(self):
        log.info("Destroying core...")
        await self.stop(IOpenFreebuds.STATE_DESTROYED)
        if self.server_task is not None:
            self.server_task.cancel("stop() requested")
            await self.server_task
        log.info("Bye-bye")

    @rpc
    async def stop(self, e_state: int = IOpenFreebuds.STATE_STOPPED):
        await self._set_state(e_state)
        if self._task is None:
            return

        log.info("Stopping core...")
        self._task.cancel("stop() requested")
        await self._task

        if self._driver is not None:
            log.info("Stopping driver...")
            await self._driver.stop()

        self._driver = None
        self._task = None
        self._device_tags = "", ""
        log.info("Stopped")

    @rpc
    async def get_device_tags(self):
        return self._device_tags

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

    @rpc
    async def run_shortcut(self, *args):
        log.info(f"Execute shortcut action {args}")
        return await self._shortcuts.execute(*args)

    @asynccontextmanager
    async def locked_device(self):
        try:
            await self._set_paused(True)
            yield
        finally:
            await self._set_paused(False)

    @rpc
    async def _set_paused(self, value: bool):
        log.info(f"Core pause value={value}")
        self._paused = value
        await self._set_state(OpenFreebuds.STATE_PAUSED)
        if value and self._driver.started:
            await self._driver.stop()

    async def _mainloop(self):
        try:
            await self._mainloop_inner()
        except asyncio.CancelledError:
            pass

    async def _mainloop_inner(self):
        log.info(f"Started")

        while True:
            if self._paused:
                log.info("Core paused...")
                await asyncio.sleep(2)
                continue

            if not await openfreebuds_backend.bt_is_connected(self._driver.device_address):
                await self._set_state(OpenFreebuds.STATE_DISCONNECTED)
                if self._driver.started:
                    log.info("Device disconnected from OS, stop driver...")
                    await self._driver.stop()
                    log.info("Driver stopped")
                await asyncio.sleep(10)
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
