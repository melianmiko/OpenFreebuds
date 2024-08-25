import asyncio
import socket

from openfreebuds.driver.generic import FbDriverGeneric
from openfreebuds.exceptions import FbStartupError
from openfreebuds.utils.logger import create_logger
from contextlib import suppress

log = create_logger("FbDriverSppGeneric")


class FbDriverSppGeneric(FbDriverGeneric):
    def __init__(self, address):
        super().__init__(address)
        self.__task_recv: asyncio.Task | None = None

        self._spp_service_uuid: str = ""
        self._spp_service_port: int = 16
        self._spp_connect_delay: int = 0
        self._writer: asyncio.StreamWriter | None = None

    async def start(self):
        try:
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(2)
            await asyncio.sleep(self._spp_connect_delay)

            sock.connect(await self.__get_sdp_result())
            reader, writer = await asyncio.open_connection(sock=sock)
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError, ValueError):
            log.exception("Driver startup failed")
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

        self._writer.close()
        # await self._writer.wait_closed()

        self._writer = None
        self.started = False
        log.info("Stopped")

    async def _loop_recv(self, reader):
        log.info(f"Init recv task with {reader}")
        await asyncio.sleep(60)

    async def __get_sdp_result(self):
        try:
            import bluetooth
            service_data = bluetooth.find_service(address=self.device_address,
                                                  uuid=self._spp_service_uuid)

            assert len(service_data) > 0
            host = service_data[0]['host']
            port = service_data[0]['port']
            log.info(f"Found serial port {host}:{port} from UUID")
        except (AssertionError, NameError, ImportError, ValueError) as e:
            log.error(f"\n\nCan't fetch service info from device, err: {e}\n"
                      "Looks like pybluez didn't installed or didn't work as expected.\n"
                      f"Using built-in port number {self._spp_service_port}\n  ")

            host = self.device_address
            port = self._spp_service_port

        return host, port
