import asyncio
import socket
from contextlib import suppress

from openfreebuds.driver.generic import OfbDriverGeneric
from openfreebuds.exceptions import FbStartupError
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbDriverSppGeneric")


class OfbDriverSppGeneric(OfbDriverGeneric):
    def __init__(self, address):
        super().__init__(address)
        self.__task_recv: asyncio.Task | None = None

        self._spp_service_port: int = 16
        self._spp_connect_delay: int = 0
        self._last_start_error: str | None = None
        self._socket: socket.socket | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def get_health_report(self):
        return {
            **(await super().get_health_report()),
            "recv_task_alive": self.__task_recv is not None and not self.__task_recv.done(),
            "last_start_error": self._last_start_error,
        }

    async def is_device_online(self):
        # Trust an active SPP session over the platform connection status.
        # On Windows the WinRT connection_status may report DISCONNECTED for
        # Dual-Connect capable devices (e.g. HUAWEI FreeBuds Pro 5) once their
        # active audio is switched to another paired device, even though the
        # SPP control channel stays fully usable. Without this fallback the
        # manager would tear down a perfectly healthy driver.
        if self.healthy():
            return True
        return await super().is_device_online()

    async def start(self):
        await self._close_transport()
        self._last_start_error = None
        try:
            self._socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self._socket.settimeout(2)
            await asyncio.sleep(self._spp_connect_delay)

            self._socket.connect((self.device_address, self._spp_service_port))
            reader, writer = await asyncio.open_connection(sock=self._socket)
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError, ValueError) as exc:
            self._last_start_error = (
                f"RFCOMM port {self._spp_service_port}: {exc.__class__.__name__}: {exc}"
            )
            await self._close_transport()
            raise FbStartupError(f"Driver startup failed ({self._last_start_error})") from exc

        self.__task_recv = asyncio.create_task(self._loop_recv(reader))
        self._writer = writer
        self.started = True
        log.info("Started")

    async def stop(self):
        await super().stop()
        await self._close_transport()
        self.started = False
        log.info("Stopped")

    def healthy(self):
        return self.started and not self.__task_recv.done()

    async def _close_transport(self):
        if self.__task_recv:
            self.__task_recv.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await self.__task_recv
            self.__task_recv = None

        if self._writer is not None:
            self._writer.close()
            with suppress(Exception):
                await self._writer.wait_closed()
            self._writer = None

        if self._socket is not None:
            with suppress(Exception):
                self._socket.shutdown(socket.SHUT_RDWR)
            with suppress(Exception):
                self._socket.close()
            self._socket = None

    async def _loop_recv(self, reader):
        log.debug(f"Init recv task with {reader}")
        await asyncio.sleep(60)
