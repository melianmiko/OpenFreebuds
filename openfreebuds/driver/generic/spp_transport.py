import asyncio
import ctypes
import errno
import os
import select
import socket
import struct
import sys
from typing import Protocol

# Linux values, for Python builds without Bluetooth support (python-build-standalone in the AppImage)
LINUX_AF_BLUETOOTH = 31
LINUX_BTPROTO_RFCOMM = 3


class SppTransport(Protocol):
    async def open(
        self,
        address: str,
        channel: int,
        *,
        connect_delay: float = 0,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]: ...


def rfcomm_sockaddr(address: str, channel: int) -> bytes:
    """struct sockaddr_rc for the Linux kernel"""
    bdaddr = bytes(reversed(bytes.fromhex(address.replace(":", ""))))
    return struct.pack("<H6sBx", LINUX_AF_BLUETOOTH, bdaddr, channel)


def _connect_rfcomm(sock: socket.socket, address: str, channel: int, timeout: float):
    """connect() through libc, since Python can't parse an AF_BLUETOOTH address without Bluetooth support"""
    libc = ctypes.CDLL(None, use_errno=True)
    addr = rfcomm_sockaddr(address, channel)
    sock.setblocking(False)
    if libc.connect(sock.fileno(), addr, len(addr)) != 0:
        err = ctypes.get_errno()
        if err != errno.EINPROGRESS:
            raise OSError(err, os.strerror(err))
        _, writable, _ = select.select([], [sock], [], timeout)
        if not writable:
            raise TimeoutError("RFCOMM connect timed out")
        err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            raise OSError(err, os.strerror(err))


class _BluetoothSocketTransport:
    """SPP transport backed by Python's stdlib AF_BLUETOOTH socket (Linux, Windows)."""

    async def open(self, address, channel, *, connect_delay=0):
        if connect_delay:
            await asyncio.sleep(connect_delay)

        if hasattr(socket, "AF_BLUETOOTH"):
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(2)
            sock.connect((address, channel))
        else:
            sock = socket.socket(LINUX_AF_BLUETOOTH, socket.SOCK_STREAM, LINUX_BTPROTO_RFCOMM)
            try:
                _connect_rfcomm(sock, address, channel, 2)
            except Exception:
                sock.close()
                raise
        return await asyncio.open_connection(sock=sock)


def get_default_transport() -> SppTransport:
    if sys.platform == "darwin":
        from openfreebuds_backend.darwin.rfcomm_transport import IOBluetoothRFCOMMTransport
        return IOBluetoothRFCOMMTransport()
    return _BluetoothSocketTransport()
