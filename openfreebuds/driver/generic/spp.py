import asyncio
import errno
from contextlib import suppress

from openfreebuds.driver.generic import OfbDriverGeneric
from openfreebuds.driver.generic.spp_transport import get_default_transport
from openfreebuds.exceptions import FbStartupError
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbDriverSppGeneric")

SPP_PORT_BUSY = "spp_port_busy"


def is_port_busy_error(error: OSError) -> bool:
    """Windows reports a taken RFCOMM endpoint as WSAEADDRINUSE (10048); POSIX uses EADDRINUSE."""
    return getattr(error, "winerror", None) == 10048 or \
        getattr(error, "errno", None) in (10048, errno.EADDRINUSE)


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
            reader, writer = await get_default_transport().open(
                self.device_address,
                self._spp_service_port,
                connect_delay=self._spp_connect_delay,
            )
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError, ValueError) as e:
            # Do not swallow errors like 10048; otherwise the UI only sees 'Driver startup failed' with no diagnostic
            log.error(f"SPP connect to {self.device_address}:{self._spp_service_port} failed: {e!r}")
            if isinstance(e, OSError) and is_port_busy_error(e):
                raise FbStartupError(SPP_PORT_BUSY)
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
            with suppress(Exception):
                # Wait until the underlying socket is really closed before the next connect/device switch;
                # otherwise the old endpoint remains allocated and hits 10048.
                await self._writer.wait_closed()

        self._writer = None
        self.started = False
        log.info("Stopped")

    def healthy(self):
        return self.started and not self.__task_recv.done()

    async def _loop_recv(self, reader):
        log.debug(f"Init recv task with {reader}")
        await asyncio.sleep(60)
