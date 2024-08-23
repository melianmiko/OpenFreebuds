import asyncio

from openfreebuds.driver.generic import FbDriverHandlerGeneric, FbDriverSppGeneric
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import FbNotReadyError, FbStartupError, FbDriverError, FbPackageChecksumError
from openfreebuds.utils.logger import create_logger

log = create_logger("FbDriverHuaweiGeneric")


class FbHuaweiResponseReceiver(asyncio.Event):
    def __init__(self):
        super().__init__()
        self.package: HuaweiSppPackage | None = None


class FbDriverHuaweiGeneric(FbDriverSppGeneric):
    INIT_ATTEMPTS = 5
    INIT_TIMEOUT = 3

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
            log.info(f'Attach handler "{handler.handler_id}"')
            handler.driver = self

            self._add_set_property_handler(handler)
            self._add_on_package_handler(handler)

        # Init all handlers
        for handler in self.handlers:
            attempt = 0
            while attempt < FbDriverHuaweiGeneric.INIT_ATTEMPTS:
                # noinspection PyBroadException
                try:
                    log.debug(f'Initializing {handler.handler_id}...')
                    async with asyncio.timeout(FbDriverHuaweiGeneric.INIT_TIMEOUT):
                        await handler.on_init()
                    break
                except TimeoutError:
                    log.debug(f'Init of "{handler.handler_id}" timed out, attempt={attempt}')
                    attempt += 1
                except Exception:
                    log.exception(f'Init of "{handler.handler_id}" failed, attempt={attempt}')
                    attempt += 1

            if attempt == FbDriverHuaweiGeneric.INIT_ATTEMPTS:
                log.exception(f'Can\'t initialize "{handler.handler_id}". Skipping.')

    async def stop(self):
        await super().stop()
        self.__on_package_handlers = {}

    async def send_package(self, pkg: HuaweiSppPackage, timeout: int = 5) -> HuaweiSppPackage | None:
        if pkg.response_id == b"":
            return await self._send_nowait(pkg)

        while pkg.response_id in self.__pending_responses:
            log.info(f"Response read conflict with {pkg.response_id}, wait for parent before continue")
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
        try:
            await self._loop_recv_inner(reader)
        except asyncio.CancelledError:
            pass

    async def _loop_recv_inner(self, reader: asyncio.StreamReader):
        while True:
            result = await self.__recv_pacakge(reader)
            if result is None:
                raise FbStartupError

    async def __recv_pacakge(self, reader: asyncio.StreamReader):
        try:
            async with asyncio.timeout(2):
                heading = await reader.read(4)
                if heading[0:2] == b"Z\x00":
                    length = heading[2]
                    if length < 4:
                        await reader.read(length)
                    else:
                        pkg = heading + await reader.read(length)
                        await self._handle_raw_pkg(pkg)
        except asyncio.TimeoutError:
            # Socket timed out, do nothing
            return False
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            # Something bad happened, exiting...
            return None

        return True

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

    async def on_init(self):
        pass

    async def on_package(self, package: HuaweiSppPackage):
        pass


_empty_handler = FbDriverHandlerHuawei()
