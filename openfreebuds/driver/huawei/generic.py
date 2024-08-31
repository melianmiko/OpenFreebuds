import asyncio

from openfreebuds.driver.generic import FbDriverHandlerGeneric, FbDriverSppGeneric
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import FbNotReadyError, FbPackageChecksumError
from openfreebuds.utils.logger import create_logger

log = create_logger("FbDriverHuaweiGeneric")


class FbHuaweiResponseReceiver(asyncio.Event):
    def __init__(self):
        super().__init__()
        self.package: HuaweiSppPackage | None = None


class FbDriverHuaweiGeneric(FbDriverSppGeneric):
    def __init__(self, address):
        super().__init__(address)
        self.__pending_responses: dict[bytes, FbHuaweiResponseReceiver] = {}
        self.__on_package_handlers: dict[bytes, FbDriverHandlerHuawei] = {}

        self._spp_service_uuid = "00001101-0000-1000-8000-00805f9b34fb"

        self.handlers: list[FbDriverHandlerHuawei] = []

    async def start(self):
        await super().start()
        await self._start_all_handlers()

    async def _start_all_handlers(self):
        # Bind all handlers
        for handler in self.handlers:
            log.debug(f'Attach handler "{handler.handler_id}"')
            handler.driver = self

            self._add_set_property_handler(handler)
            self._add_on_package_handler(handler)

        # Init all handlers
        for handler in self.handlers:
            await handler.init()

    async def stop(self):
        await super().stop()
        self.__on_package_handlers = {}

    async def send_package(self, pkg: HuaweiSppPackage, timeout: int = 5) -> HuaweiSppPackage | None:
        if pkg.response_id == b"":
            return await self._send_nowait(pkg)

        while pkg.response_id in self.__pending_responses:
            log.debug(f"Response read conflict with {pkg.response_id}, wait for parent before continue")
            await self.__pending_responses[pkg.response_id].wait()
            await asyncio.sleep(0.5)

        event = FbHuaweiResponseReceiver()
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

        log.debug(f"TX {pkg.to_bytes().hex()}\n{pkg}")
        self._writer.write(pkg.to_bytes())
        await self._writer.drain()

    async def _handle_raw_pkg(self, pkg):
        try:
            pkg = HuaweiSppPackage.from_bytes(pkg)
            log.debug(f"RX {pkg.to_bytes().hex()}\n{pkg}")
        except (AssertionError, FbPackageChecksumError):
            log.exception(f"Got non-parsable package {pkg.hex()}, ignoring")
            return

        if pkg.command_id in self.__pending_responses:
            self.__pending_responses[pkg.command_id].package = pkg
            self.__pending_responses[pkg.command_id].set()
        elif pkg.command_id in self.__on_package_handlers:
            await self.__on_package_handlers[pkg.command_id].on_package(pkg)
        else:
            log.info(f"Got unsupported package\n{str(pkg)}")

    async def _loop_recv(self, reader: asyncio.StreamReader):
        while True:
            try:
                await self.__recv_pacakge(reader)
            except asyncio.TimeoutError:
                pass
            except (asyncio.CancelledError, ConnectionResetError, ConnectionAbortedError, OSError):
                log.debug(f"Stop recv loop due to connection failure")
                return
            except Exception:
                log.exception("Unknown exception in recv loop")
                await asyncio.sleep(2)

    async def __recv_pacakge(self, reader: asyncio.StreamReader):
        async with asyncio.timeout(5):
            heading = await reader.read(4)
            if len(heading) == 0:
                log.debug("Got empty package, seems like socked is closed")
                raise ConnectionResetError
            if heading[0:2] == b"Z\x00":
                length = heading[2]
                if length < 4:
                    await reader.read(length)
                else:
                    pkg = heading + await reader.read(length)
                    await self._handle_raw_pkg(pkg)

    def _add_on_package_handler(self, handler):
        for pkg_id in handler.commands:
            self.__on_package_handlers[pkg_id] = handler
        for pkg_id in handler.ignore_commands:
            self.__on_package_handlers[pkg_id] = _empty_handler


class FbDriverHandlerHuawei(FbDriverHandlerGeneric):
    handler_id: str = ""
    commands: list[bytes] = []
    ignore_commands: list[bytes] = []
    driver: FbDriverHuaweiGeneric = None

    init_timeout: int = 3
    init_attempt: int = 0
    init_attempt_max: int = 5

    async def init(self):
        self.init_attempt = 0
        while self.init_attempt < self.init_attempt_max:
            # noinspection PyBroadException
            try:
                log.debug(f'Initializing {self.handler_id}...')
                async with asyncio.timeout(self.init_timeout):
                    await self.on_init()
                break
            except TimeoutError:
                log.debug(f'Init of "{self.handler_id}" timed out, attempt={self.init_attempt}')
                self.init_attempt += 1
            except Exception:
                log.exception(f'Init of "{self.handler_id}" failed, attempt={self.init_attempt}')
                self.init_attempt += 1

        if self.init_attempt == self.init_attempt_max:
            log.exception(f'Can\'t initialize "{self.handler_id}". Skipping.')

    async def on_init(self):
        pass

    async def on_package(self, package: HuaweiSppPackage):
        pass


_empty_handler = FbDriverHandlerHuawei()