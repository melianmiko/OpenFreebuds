import asyncio
from contextlib import asynccontextmanager

from openfreebuds.driver.generic import OfbDriverHandlerGeneric, OfbDriverSppGeneric
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import FbNotReadyError, OfbPackageChecksumError
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbDriverHuaweiGeneric")

# FreeClip 2 的 EQ 写入（0x2B49）有时不回 ACK，而是回一条 0x2B4A 状态通知。
# 收到 0x2B4A 时同时唤醒等待 0x2B49 的调用，避免 UI 白等 5 秒超时。
_RESPONSE_ALIASES = {
    b"\x2b\x4a": b"\x2b\x49",
}


class OfbHuaweiResponseReceiver(asyncio.Event):
    def __init__(self):
        super().__init__()
        self.package: HuaweiSppPackage | None = None


class OfbDriverHuaweiGeneric(OfbDriverSppGeneric):
    def __init__(self, address):
        super().__init__(address)
        self.__pending_responses: dict[bytes, OfbHuaweiResponseReceiver] = {}
        self.__on_package_handlers: dict[bytes, list[OfbDriverHandlerHuawei]] = {}
        self.__raw_sessions: dict[bytes, asyncio.Queue] = {}
        self._raw_all_queue: asyncio.Queue | None = None

        # self._spp_service_uuid = "00001101-0000-1000-8000-00805f9b34fb"

        self.handlers: list[OfbDriverHandlerHuawei] = []

    async def start(self):
        await super().start()
        await self._start_all_handlers()

    async def get_health_report(self):
        return {
            **(await super().get_health_report()),
            "spp_port": self._spp_service_port,
            "pending_responses_count": len(self.__pending_responses.values()),
            "handlers": [h.get_report() for h in self.handlers],
        }

    async def _start_all_handlers(self):
        # Bind all handlers
        for handler in self.handlers:
            log.debug(f'Attach handler "{handler.handler_id}"')
            handler.driver = self

            self._add_set_property_handler(handler)
            self._add_on_package_handler(handler)

        # Init all handlers
        for handler in self.handlers:
            try:
                await handler.init()
            except Exception:
                log.exception(f"Init of {handler.handler_id} failed")

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

        event = OfbHuaweiResponseReceiver()
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

    async def send_raw_recv(self, cmd: bytes, framed: bytes, timeout: int = 5) -> HuaweiSppPackage | None:
        """发送原始帧（已含 0x5A 头与 CRC）并等待同命令字的下一帧响应。

        用于提示音上传等非标准 TLV 通路：先登记接收器再发送，避免响应竞态。
        """
        async with self.raw_session(cmd) as session:
            await session.send_framed(framed)
            return await session.recv(timeout)

    @asynccontextmanager
    async def raw_session(self, cmd: bytes):
        """为某命令字开启原始帧会话，期间该命令字的入站帧进入队列而非分发到 handler。"""
        queue: asyncio.Queue = asyncio.Queue()
        self.__raw_sessions[cmd] = queue
        try:
            yield _RawSession(self, queue)
        finally:
            self.__raw_sessions.pop(cmd, None)

    @asynccontextmanager
    async def raw_session_all(self):
        """捕获**所有**入站帧（不分命令字）的原始会话。

        提示音 proto2 上传要同时盯 09 01/09 0a/09 02/09 03/09 05 多个命令字，
        按命令字过滤的 raw_session 收不全，用这个。
        """
        queue: asyncio.Queue = asyncio.Queue()
        self._raw_all_queue = queue
        try:
            yield _RawSession(self, queue)
        finally:
            self._raw_all_queue = None

    async def _handle_raw_pkg(self, pkg):
        try:
            pkg = HuaweiSppPackage.from_bytes(pkg)
            log.debug(f"RX {pkg}")
        except (AssertionError, OfbPackageChecksumError):
            log.info(f"Got non-parsable package {pkg.hex()}, ignoring")
            return

        if self._raw_all_queue is not None:
            self._raw_all_queue.put_nowait(pkg)
        elif pkg.command_id in self.__raw_sessions:
            self.__raw_sessions[pkg.command_id].put_nowait(pkg)
        elif pkg.command_id in self.__pending_responses:
            self.__pending_responses[pkg.command_id].package = pkg
            self.__pending_responses[pkg.command_id].set()
        elif pkg.command_id in self.__on_package_handlers:
            # 0x2B4A 等通知也可以作为等待中写命令的完成信号
            self._resolve_response_alias(pkg)
            for handler in self.__on_package_handlers[pkg.command_id]:
                await handler.on_package(pkg)
        else:
            log.warn(f"Got unsupported package\n{str(pkg)}")

    def _resolve_response_alias(self, pkg: HuaweiSppPackage):
        alias = _RESPONSE_ALIASES.get(pkg.command_id)
        if alias is None:
            return
        receiver = self.__pending_responses.get(alias)
        if receiver is None:
            return
        log.debug(f"Resolve pending {alias!r} with alias notification {pkg.command_id!r}")
        receiver.package = pkg
        receiver.set()

    async def _loop_recv(self, reader: asyncio.StreamReader):
        while True:
            try:
                await self.__recv_pacakge(reader)
            except (asyncio.CancelledError, ConnectionResetError, ConnectionAbortedError, OSError):
                log.debug(f"Stop recv loop due to connection failure")
                return
            except Exception:
                log.exception("Unknown exception in recv loop")
                await asyncio.sleep(2)

    async def __recv_pacakge(self, reader: asyncio.StreamReader):
        heading = await reader.read(4)
        if len(heading) == 0:
            log.debug("Got empty package, seems like socked is closed")
            raise ConnectionResetError
        if heading[0] == 0x5A:
            length = int.from_bytes(heading[1:3], byteorder="big")
            if length < 4:
                await reader.read(length)
            else:
                pkg = heading + await reader.read(length)
                await self._handle_raw_pkg(pkg)

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


class _RawSession:
    def __init__(self, driver: OfbDriverHuaweiGeneric, queue: asyncio.Queue):
        self._driver = driver
        self._queue = queue

    async def send_framed(self, framed: bytes):
        if not self._driver._writer:
            raise FbNotReadyError("Can't send package before SPP start")
        self._driver._writer.write(framed)
        await self._driver._writer.drain()

    async def recv(self, timeout: int = 5) -> HuaweiSppPackage | None:
        try:
            async with asyncio.timeout(timeout):
                return await self._queue.get()
        except TimeoutError:
            return None
