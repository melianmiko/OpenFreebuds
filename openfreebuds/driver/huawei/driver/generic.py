import asyncio
from collections.abc import Callable
from contextlib import suppress

from openfreebuds.driver.generic import OfbDriverHandlerGeneric, OfbDriverSppGeneric
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import FbNotReadyError, OfbPackageChecksumError
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbDriverHuaweiGeneric")


class OfbHuaweiResponseReceiver(asyncio.Event):
    def __init__(self, matcher: Callable[[HuaweiSppPackage], bool] | None = None):
        super().__init__()
        self.package: HuaweiSppPackage | None = None
        self.matcher = matcher

    def matches(self, package: HuaweiSppPackage) -> bool:
        return self.matcher is None or self.matcher(package)


class OfbDriverHuaweiGeneric(OfbDriverSppGeneric):
    def __init__(self, address):
        super().__init__(address)
        self.__pending_responses: dict[bytes, OfbHuaweiResponseReceiver] = {}
        self.__on_package_handlers: dict[bytes, list[OfbDriverHandlerHuawei]] = {}
        self._handlers_init_task: asyncio.Task | None = None

        # self._spp_service_uuid = "00001101-0000-1000-8000-00805f9b34fb"

        self.handlers: list[OfbDriverHandlerHuawei] = []

    async def start(self):
        await super().start()
        self._bind_all_handlers()
        self._handlers_init_task = asyncio.create_task(self._init_all_handlers())

    async def get_health_report(self):
        return {
            **(await super().get_health_report()),
            "spp_port": self._spp_service_port,
            "pending_responses_count": len(self.__pending_responses.values()),
            "handlers_init_task_alive": self._handlers_init_task is not None and not self._handlers_init_task.done(),
            "handlers": [h.get_report() for h in self.handlers],
        }

    def _bind_all_handlers(self):
        # Bind all handlers
        for handler in self.handlers:
            log.debug(f'Attach handler "{handler.handler_id}"')
            handler.driver = self

            self._add_set_property_handler(handler)
            self._add_on_package_handler(handler)

    async def _start_all_handlers(self):
        self._bind_all_handlers()
        await self._init_all_handlers()

    async def _init_all_handlers(self):
        # Init all handlers
        for handler in self.handlers:
            try:
                await handler.init()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception(f"Init of {handler.handler_id} failed")

    async def stop(self):
        if self._handlers_init_task is not None:
            self._handlers_init_task.cancel("driver stop requested")
            with suppress(asyncio.CancelledError):
                await self._handlers_init_task
            self._handlers_init_task = None

        await super().stop()
        self.__on_package_handlers = {}

    async def send_package(
            self,
            pkg: HuaweiSppPackage,
            timeout: int = 5,
            response_matcher: Callable[[HuaweiSppPackage], bool] | None = None,
    ) -> HuaweiSppPackage | None:
        if pkg.response_id == b"":
            return await self._send_nowait(pkg)

        while pkg.response_id in self.__pending_responses:
            log.debug(f"Response read conflict with {pkg.response_id}, wait for parent before continue")
            await self.__pending_responses[pkg.response_id].wait()
            await asyncio.sleep(0.5)

        event = OfbHuaweiResponseReceiver(response_matcher)
        try:
            self.__pending_responses[pkg.response_id] = event
            await self._send_nowait(pkg)
            async with asyncio.timeout(timeout):
                await event.wait()
        finally:
            # Free up awaiter
            self.__pending_responses[pkg.response_id].set()
            del self.__pending_responses[pkg.response_id]
        return event.package

    async def _send_nowait(self, pkg: HuaweiSppPackage):
        if not self._writer:
            raise FbNotReadyError("Can't send package before SPP start")

        log.debug(f"TX {pkg}")
        self._writer.write(pkg.to_bytes())
        await self._writer.drain()

    async def _handle_raw_pkg(self, pkg):
        try:
            pkg = HuaweiSppPackage.from_bytes(pkg)
            log.debug(f"RX {pkg}")
        except (AssertionError, OfbPackageChecksumError):
            log.info(f"Got non-parsable package {pkg.hex()}, ignoring")
            return

        if pkg.command_id in self.__pending_responses:
            receiver = self.__pending_responses[pkg.command_id]
            if receiver.matches(pkg):
                receiver.package = pkg
                receiver.set()
                return
            log.debug(f"RX command={pkg.command_id.hex()} does not match pending response filter, dispatching")

        if pkg.command_id in self.__on_package_handlers:
            for handler in self.__on_package_handlers[pkg.command_id]:
                await handler.on_package(pkg)
        else:
            log.warning(f"Got unsupported package\n{str(pkg)}")

    async def _loop_recv(self, reader: asyncio.StreamReader):
        while True:
            try:
                await self.__recv_package(reader)
            except (asyncio.CancelledError, ConnectionResetError, ConnectionAbortedError, OSError):
                log.debug(f"Stop recv loop due to connection failure")
                return
            except Exception:
                log.exception("Unknown exception in recv loop")
                await asyncio.sleep(2)

    async def __recv_package(self, reader: asyncio.StreamReader):
        heading = await self.__read_package_heading(reader)
        length = int.from_bytes(heading[1:3], byteorder="big")

        if length < 3:
            await self.__read_exactly(reader, length + 1)
            log.info(f"Got package with invalid length {length}, ignoring")
            return

        pkg = heading + await self.__read_exactly(reader, length + 1)
        await self._handle_raw_pkg(pkg)

    async def __read_package_heading(self, reader: asyncio.StreamReader) -> bytes:
        while True:
            marker = await self.__read_exactly(reader, 1)
            if marker != b"Z":
                log.debug(f"Skip unexpected byte {marker.hex()} while looking for package header")
                continue

            heading = marker + await self.__read_exactly(reader, 3)
            if heading[3] == 0:
                return heading

            log.debug(f"Skip package header with unsupported control byte {heading[3]:02x}")

    async def __read_exactly(self, reader: asyncio.StreamReader, size: int) -> bytes:
        try:
            return await reader.readexactly(size)
        except asyncio.IncompleteReadError as e:
            if len(e.partial) == 0:
                log.debug("Got empty package, seems like socked is closed")
            else:
                log.debug(f"Got incomplete package fragment ({len(e.partial)}/{size}), seems like socked is closed")
            raise ConnectionResetError from e

    def _add_on_package_handler(self, handler):
        for pkg_id in handler.commands:
            self.__on_package_handlers.setdefault(pkg_id, []).append(handler)
        for pkg_id in handler.ignore_commands:
            self.__on_package_handlers.setdefault(pkg_id, []).append(_empty_handler)


class OfbDriverHandlerHuawei(OfbDriverHandlerGeneric):
    handler_id: str = ""
    commands: list[bytes] = []
    ignore_commands: list[bytes] = []
    driver: OfbDriverHuaweiGeneric = None

    init_timeout: int = 3
    init_attempt: int = 0
    init_attempt_max: int = 5
    init_success: bool = False

    def get_report(self):
        return {
            "id": self.handler_id,
            "success": self.init_success,
            "attempts": self.init_attempt,
        }

    async def init(self):
        self.init_attempt = 0
        while self.init_attempt < self.init_attempt_max:
            # noinspection PyBroadException
            try:
                log.debug(f'Init {self.handler_id}, attempt={self.init_attempt}...')
                async with asyncio.timeout(self.init_timeout):
                    await self.on_init()
                break
            except (TimeoutError, ConnectionResetError):
                self.init_attempt += 1
            except Exception:
                log.exception(f"Unknown error on {self.handler_id} init")
                self.init_attempt += 1

        self.init_success = self.init_attempt != self.init_attempt_max
        if not self.init_success:
            log.info(f'Can\'t initialize "{self.handler_id}". Skipping.')

    async def on_init(self):
        pass

    async def on_package(self, package: HuaweiSppPackage):
        pass


_empty_handler = OfbDriverHandlerHuawei()
