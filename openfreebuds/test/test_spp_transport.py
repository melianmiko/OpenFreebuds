import pytest

from openfreebuds.driver.generic import spp_transport


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
