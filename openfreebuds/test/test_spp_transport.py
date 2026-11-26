import errno

import pytest

from openfreebuds.driver.generic import spp_transport
from openfreebuds.driver.generic import spp as spp_module
from openfreebuds.driver.generic.spp import OfbDriverSppGeneric, SPP_PORT_BUSY, is_port_busy_error
from openfreebuds.exceptions import FbStartupError


class _FailingSocket:
    def __init__(self):
        self.closed = False

    def settimeout(self, _value):
        pass

    def connect(self, _address):
        raise TimeoutError("timed out")

    def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_failed_connect_closes_socket(monkeypatch):
    """After a connect timeout the socket must be closed; otherwise the next Windows connect reports 10048."""
    sock = _FailingSocket()
    monkeypatch.setattr(spp_transport.socket, "socket", lambda *args: sock)

    with pytest.raises(TimeoutError):
        await spp_transport._BluetoothSocketTransport().open("00:11:22:33:44:55", 1)

    assert sock.closed


class _BusyTransport:
    async def open(self, *_args, **_kwargs):
        raise OSError(errno.EADDRINUSE, "address already in use")


def test_port_busy_detection():
    assert is_port_busy_error(OSError(errno.EADDRINUSE, "in use"))
    assert not is_port_busy_error(TimeoutError("timed out"))


@pytest.mark.asyncio
async def test_port_busy_start_reports_known_reason(monkeypatch):
    """A 10048/EADDRINUSE failure must carry a code the UI can translate, not a generic message."""
    driver = OfbDriverSppGeneric("00:11:22:33:44:55")
    monkeypatch.setattr(spp_module, "get_default_transport", lambda: _BusyTransport())

    with pytest.raises(FbStartupError) as error:
        await driver.start()

    assert error.value.args == (SPP_PORT_BUSY,)
