"""IOBluetoothRFCOMMChannel ↔ asyncio bridge.

Exposes `IOBluetoothRFCOMMTransport.open(...)` returning an asyncio
`StreamReader`-compatible reader and `StreamWriter`-compatible writer, so
[openfreebuds/driver/generic/spp.py](openfreebuds/driver/generic/spp.py) and
its subclasses work unchanged on macOS.

Implementation notes:

- IOBluetoothRFCOMMChannel delegate callbacks are delivered on the main
  thread's NSRunLoop. asyncio runs on the main thread but does not pump
  NSRunLoop, so we drive it ourselves: a recurring `loop.call_later` tick
  runs `NSRunLoop.runMode:beforeDate:` for one zero-duration iteration,
  which delivers any queued delegate callbacks without blocking.
- Synchronous IOBluetooth calls (`openConnection`, `performSDPQuery`,
  device lookup) are off-loaded via `asyncio.to_thread`.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Optional

import objc
from Foundation import (
    NSDate,
    NSDefaultRunLoopMode,
    NSObject,
    NSRunLoop,
)
import IOBluetooth

from openfreebuds_backend.darwin._sdp import find_spp_channel

log = logging.getLogger("OfbDarwinRFCOMM")

_PUMP_INTERVAL = 0.02  # 50 Hz NSRunLoop pump from asyncio


# ---------------------------------------------------------------------------
# Delegate
# ---------------------------------------------------------------------------

class _RFCOMMDelegate(NSObject):
    def initWithBridge_(self, bridge):
        self = objc.super(_RFCOMMDelegate, self).init()
        if self is None:
            return None
        self._bridge = bridge
        return self

    def rfcommChannelOpenComplete_status_(self, channel, status):
        self._bridge._on_open_complete(int(status))

    def rfcommChannelData_data_length_(self, channel, data, length):
        if isinstance(data, (bytes, bytearray)):
            chunk = bytes(data[: int(length)])
        else:
            try:
                chunk = bytes(data)
            except Exception:
                chunk = b""
        self._bridge._on_data(chunk)

    def rfcommChannelClosed_(self, channel):
        self._bridge._on_closed()

    def rfcommChannelWriteComplete_refcon_status_(self, channel, refcon, status):
        try:
            ref = int(refcon) if refcon is not None else None
        except Exception:
            ref = None
        self._bridge._on_write_complete(ref, int(status))


# ---------------------------------------------------------------------------
# Bridge — turns delegate events into asyncio futures / queue items
# ---------------------------------------------------------------------------

class _Bridge:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._queue: asyncio.Queue = asyncio.Queue()
        self._open_future: asyncio.Future = loop.create_future()
        self._write_futures: dict[int, asyncio.Future] = {}
        self._closed_flag = False

    def _on_open_complete(self, status: int):
        if self._open_future.done():
            return
        if status == 0:
            self._open_future.set_result(0)
        else:
            self._open_future.set_exception(
                ConnectionRefusedError(f"openRFCOMMChannel failed, status={status}")
            )

    def _on_data(self, chunk: bytes):
        if not chunk:
            return
        self._queue.put_nowait(chunk)

    def _on_closed(self):
        if self._closed_flag:
            return
        self._closed_flag = True
        self._queue.put_nowait(None)
        if not self._open_future.done():
            self._open_future.set_exception(ConnectionResetError("channel closed"))
        for ref, fut in list(self._write_futures.items()):
            if not fut.done():
                fut.set_exception(ConnectionResetError("channel closed"))
            self._write_futures.pop(ref, None)

    def _on_write_complete(self, ref, status: int):
        if ref is None:
            return
        fut = self._write_futures.pop(ref, None)
        if fut is None or fut.done():
            return
        if status == 0:
            fut.set_result(None)
        else:
            fut.set_exception(OSError(f"RFCOMM write failed, status={status}"))


# ---------------------------------------------------------------------------
# StreamReader/StreamWriter look-alikes
# ---------------------------------------------------------------------------

class _RFCOMMReader:
    def __init__(self, bridge: _Bridge):
        self._bridge = bridge
        self._buffer = bytearray()
        self._eof = False

    async def read(self, n: int = -1) -> bytes:
        if n == 0:
            return b""
        while not self._buffer and not self._eof:
            chunk = await self._bridge._queue.get()
            if chunk is None:
                self._eof = True
                break
            self._buffer.extend(chunk)
        if not self._buffer:
            return b""
        if n < 0 or n >= len(self._buffer):
            out = bytes(self._buffer)
            self._buffer.clear()
            return out
        out = bytes(self._buffer[:n])
        del self._buffer[:n]
        return out


class _RFCOMMWriter:
    def __init__(self, transport: "IOBluetoothRFCOMMTransport", bridge: _Bridge):
        self._transport = transport
        self._bridge = bridge
        self._pending: list[asyncio.Future] = []
        self._closing = False

    def write(self, data) -> None:
        if self._closing:
            raise ConnectionResetError("writer is closing")
        if not data:
            return
        fut = self._transport._submit_write(bytes(data))
        self._pending.append(fut)

    async def drain(self) -> None:
        if not self._pending:
            return
        pending, self._pending = self._pending, []
        for fut in pending:
            await fut

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._transport._close()

    def is_closing(self) -> bool:
        return self._closing


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

class IOBluetoothRFCOMMTransport:
    """Single-use RFCOMM transport. Create one per OpenFreebuds driver instance."""

    def __init__(self):
        self._channel = None
        self._delegate: Optional[_RFCOMMDelegate] = None
        self._bridge: Optional[_Bridge] = None
        self._next_refcon = 1
        self._stopped = False
        self._pump_handle: Optional[asyncio.TimerHandle] = None

    async def open(
        self,
        address: str,
        channel: int,
        *,
        connect_delay: float = 0,
    ) -> tuple[_RFCOMMReader, _RFCOMMWriter]:
        loop = asyncio.get_running_loop()
        self._bridge = _Bridge(loop)

        device = await asyncio.to_thread(_get_device, address)
        if device is None:
            raise ConnectionRefusedError(f"Bluetooth device not found: {address}")

        if not bool(device.isConnected()):
            log.info(f"Device {address} is not connected; calling openConnection()")
            err = await asyncio.to_thread(device.openConnection)
            if err != 0:
                raise ConnectionRefusedError(f"openConnection failed: {err}")

        # Start the NSRunLoop pump *before* opening the channel so we don't
        # miss the openComplete delegate callback.
        self._start_pump(loop)

        with suppress(Exception):
            await asyncio.to_thread(device.performSDPQuery_, None)

        resolved = await asyncio.to_thread(find_spp_channel, device, channel)
        if resolved is None:
            log.warning(
                f"SDP lookup found no SPP service on {address}; "
                f"falling back to channel {channel}"
            )
            resolved = channel
        log.info(f"Opening RFCOMM channel {resolved} on {address}")

        if connect_delay:
            await asyncio.sleep(connect_delay)

        self._delegate = _RFCOMMDelegate.alloc().initWithBridge_(self._bridge)
        err, ch = device.openRFCOMMChannelSync_withChannelID_delegate_(
            None, int(resolved), self._delegate
        )
        if err != 0:
            self._stop_pump()
            raise ConnectionRefusedError(f"openRFCOMMChannelSync failed, err={err}")
        self._channel = ch

        try:
            await asyncio.wait_for(self._bridge._open_future, timeout=10)
        except asyncio.TimeoutError:
            self._stop_pump()
            raise ConnectionRefusedError("RFCOMM channel open timed out")

        return _RFCOMMReader(self._bridge), _RFCOMMWriter(self, self._bridge)

    # ------------------------------------------------------------------
    def _start_pump(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._pump_handle is not None:
            return
        self._pump_handle = loop.call_soon(self._pump, loop)

    def _stop_pump(self) -> None:
        self._stopped = True
        if self._pump_handle is not None:
            with suppress(Exception):
                self._pump_handle.cancel()
            self._pump_handle = None

    def _pump(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._stopped:
            return
        try:
            NSRunLoop.currentRunLoop().runMode_beforeDate_(
                NSDefaultRunLoopMode,
                NSDate.dateWithTimeIntervalSinceNow_(0),
            )
        except Exception:
            log.exception("NSRunLoop pump raised")
        if not self._stopped:
            self._pump_handle = loop.call_later(_PUMP_INTERVAL, self._pump, loop)

    # ------------------------------------------------------------------
    def _submit_write(self, data: bytes) -> asyncio.Future:
        assert self._bridge is not None
        loop = self._bridge._loop
        if self._channel is None or self._stopped:
            fut = loop.create_future()
            fut.set_exception(ConnectionResetError("channel closed"))
            return fut
        ref = self._next_refcon
        self._next_refcon += 1
        fut = loop.create_future()
        self._bridge._write_futures[ref] = fut
        try:
            err = self._channel.writeAsync_length_refcon_(data, len(data), ref)
        except Exception as e:
            log.exception("writeAsync raised")
            self._bridge._on_write_complete(ref, -1)
            return fut
        if err != 0:
            self._bridge._on_write_complete(ref, int(err))
        return fut

    # ------------------------------------------------------------------
    def _close(self) -> None:
        if self._stopped:
            return
        if self._channel is not None:
            with suppress(Exception):
                self._channel.closeChannel()
        self._stop_pump()


def _get_device(address: str):
    addr = address.replace("-", ":").upper()
    return IOBluetooth.IOBluetoothDevice.deviceWithAddressString_(addr) or \
        IOBluetooth.IOBluetoothDevice.deviceWithAddressString_(addr.replace(":", "-").lower())
