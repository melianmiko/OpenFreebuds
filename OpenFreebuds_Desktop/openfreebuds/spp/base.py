import logging
import socket
import threading
import traceback

from openfreebuds import protocol_utils

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
        self.started = False
        self.socket = None

        self._properties = {}
        self.on_property_change = threading.Event()
        self.on_recv = threading.Event()
        self.on_close = threading.Event()
        self._on_thread_exit = threading.Event()

    def connect(self):
        if self.on_close.is_set():
            raise Exception("Can't reuse exiting device object")

        try:
            self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
                                        socket.BTPROTO_RFCOMM)
            self.socket.connect((self.address, port))

            threading.Thread(target=self._mainloop).start()
            self.on_init()

            return True
        except (ConnectionResetError, ConnectionRefusedError, OSError):
            self.close()
            return False

    def close(self):
        # Raise all events to unlock all waiting threads
        self.on_property_change.set()
        self.on_recv.set()

        if self.started:
            log.info("closing...")
            self.started = False
            self.socket.close()
            self._on_thread_exit.wait()

            log.info("closed successfully")

        self.on_close.set()

    def _mainloop(self):
        self.started = True
        self.socket.settimeout(2)

        log.info("starting recv...")

        while self.started:
            try:
                byte = self.socket.recv(4)
                if byte[0:2] == b"Z\x00":
                    length = byte[2]
                    if length < 4:
                        self.socket.recv(length)
                    else:
                        pkg = self.socket.recv(length)
                        log.debug("recv " + pkg.hex())
                        self.on_package(pkg)
            except (TimeoutError, socket.timeout):
                # Socket timed out, do nothing
                pass
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                # Something bad happened, exiting...
                break

        self._on_thread_exit.set()
        self.close()
        log.info("Leaving recv...")

    def send_command(self, data, read=False):
        self.send(build_spp_bytes(data))

        if read:
            self.on_recv.wait()
            self.on_property_change.clear()

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
        self.on_property_change.set()

    def set_property(self, prop, value):
        raise "Must be override"

    def on_init(self):
        raise "Must be override"

    def on_package(self, pkg):
        raise "Must be override"
