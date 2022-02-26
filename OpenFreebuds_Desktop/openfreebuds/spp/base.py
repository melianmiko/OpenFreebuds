import logging
import socket
import threading

from openfreebuds import protocol_utils, event_bus
from openfreebuds.events import EVENT_SPP_CLOSED, EVENT_SPP_RECV, EVENT_DEVICE_PROP_CHANGED

log = logging.getLogger("SPPDevice")

uuid = "00001101-0000-1000-8000-00805f9b34fb"
port = 16


def build_spp_bytes(data):
    out = b"Z"
    out += (len(data) + 1).to_bytes(2, byteorder="big") + b"\x00"
    out += protocol_utils.array2bytes(data)

    checksum = protocol_utils.crc16char(out)
    out += (checksum >> 8).to_bytes(1, "big")
    out += (checksum & 0b11111111).to_bytes(1, "big")

    return out


# noinspection PyMethodMayBeStatic
class BaseSPPDevice:

    def __init__(self, address):
        self.last_pkg = None
        self.address = address
        self.closed = False
        self.socket = None
        self.safe_run_wrapper = None

        self._properties = {}

    def connect(self):
        if self.closed:
            raise Exception("Can't reuse exiting device object")

        try:
            self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
                                        socket.BTPROTO_RFCOMM)
            self.socket.connect((self.address, port))

            if self.safe_run_wrapper is None:
                threading.Thread(target=self._mainloop).start()
            else:
                log.debug("Starting via safe wrapper")
                self.safe_run_wrapper(self._mainloop, "SPPDevice", False)

            self.on_init()

            return True
        except (ConnectionResetError, ConnectionRefusedError, OSError):
            log.exception("Can't create socket connection")
            self.close()
            return False

    def close(self, lock=False):
        if self.closed:
            return

        log.debug("Closing device...")
        self.closed = True
        if lock:
            event_bus.wait_for(EVENT_SPP_CLOSED)

    def _mainloop(self):
        self.socket.settimeout(2)
        log.info("starting recv...")

        while not self.closed:
            try:
                byte = self.socket.recv(4)
                if byte[0:2] == b"Z\x00":
                    length = byte[2]
                    if length < 4:
                        self.socket.recv(length)
                    else:
                        pkg = self.socket.recv(length)
                        self.on_package(pkg)
                        event_bus.invoke(EVENT_SPP_RECV)
            except (TimeoutError, socket.timeout):
                # Socket timed out, do nothing
                pass
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                # Something bad happened, exiting...
                break

        log.info("Leaving recv...")
        self.socket.close()
        self.closed = True
        event_bus.invoke(EVENT_SPP_CLOSED)

    def send_command(self, data, read=False):
        self.send(build_spp_bytes(data))

        if read:
            event_bus.wait_for(EVENT_SPP_RECV, timeout=1)

    def send(self, data):
        try:
            log.debug("send " + data.hex())
            self.socket.send(data)
        except ConnectionResetError:
            self.close()
            return

    def list_properties(self):
        return self._properties

    def get_property(self, prop, fallback=None):
        if prop not in self._properties:
            return fallback

        return self._properties[prop]

    def put_property(self, prop, value):
        self._properties[prop] = value
        log.debug("Put property " + prop + " = " + str(value))
        event_bus.invoke(EVENT_DEVICE_PROP_CHANGED)

    def set_property(self, prop, value):
        raise "Must be override"

    def on_init(self):
        raise "Must be override"

    def on_package(self, pkg):
        raise "Must be override"
