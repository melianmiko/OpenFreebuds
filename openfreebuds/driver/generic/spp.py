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
        self._writer: asyncio.StreamWriter | None = None

    async def get_health_report(self):
        return {
            **(await super().get_health_report()),
            "recv_task_alive": not self.__task_recv.done(),
        }

    async def start(self):
        try:
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(2)
            await asyncio.sleep(self._spp_connect_delay)

            sock.connect((self.device_address, self._spp_service_port))
            reader, writer = await asyncio.open_connection(sock=sock)
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError, ValueError):
            raise FbStartupError("Driver startup failed")

        self.__task_recv = asyncio.create_task(self._loop_recv(reader))
        self._writer = writer
        self.started = True
        log.info("Started")

    async def stop(self):
        await super().stop()
        if not self.started:
            return

        if self.__task_recv:
            self.__task_recv.cancel()
            with suppress(Exception):
                await self.__task_recv
            self.__task_recv = None

        if self._writer is not None:
            self._writer.close()

        self._writer = None
        self.started = False
        log.info("Stopped")

    def healthy(self):
        return self.started and not self.__task_recv.done()

    async def _loop_recv(self, reader):
        log.debug(f"Init recv task with {reader}")
        await asyncio.sleep(60)
