import asyncio
import socket
import sys
from typing import Protocol


class SppTransport(Protocol):
    async def open(
        self,
        address: str,
        channel: int,
        *,
        connect_delay: float = 0,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]: ...


class _BluetoothSocketTransport:
    """SPP transport backed by Python's stdlib AF_BLUETOOTH socket (Linux, Windows)."""

    async def open(self, address, channel, *, connect_delay=0):
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(2)
        if connect_delay:
            await asyncio.sleep(connect_delay)
        sock.connect((address, channel))
        return await asyncio.open_connection(sock=sock)


def get_default_transport() -> SppTransport:
    if sys.platform == "darwin":
        from openfreebuds_backend.darwin.rfcomm_transport import IOBluetoothRFCOMMTransport
        return IOBluetoothRFCOMMTransport()
    return _BluetoothSocketTransport()
