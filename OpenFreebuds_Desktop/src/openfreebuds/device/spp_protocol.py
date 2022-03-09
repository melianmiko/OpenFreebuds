import logging
import socket
import threading
import time

from openfreebuds import protocol_utils, event_bus
from openfreebuds.device.base import BaseDevice
from openfreebuds.events import EVENT_SPP_CLOSED, EVENT_SPP_RECV, EVENT_SPP_WAKE_UP, EVENT_SPP_ON_WAKE_UP

log = logging.getLogger("SPPDevice")
port = 16


class SppProtocolDevice(BaseDevice):
    def __init__(self, address):
        super().__init__()
        self.last_pkg = None
        self.address = address
        self.sleep = False
        self.socket = None

    def connect(self):
        if self.closed:
            raise Exception("Can't reuse exiting device object")

        try:
            self._connect_socket()

            if self.config.SAFE_RUN_WRAPPER is None:
                threading.Thread(target=self._mainloop).start()
            else:
                log.debug("Starting via safe wrapper")
                self.config.SAFE_RUN_WRAPPER(self._mainloop, "SPPDevice", False)

            self.on_init()

            return True
        except (ConnectionResetError, ConnectionRefusedError, OSError):
            log.exception("Can't create socket connection")
            self.close()
            return False

    def request_interaction(self):
        try:
            self._connect_socket()
            time.sleep(1)

            self.socket.close()
            return True
        except (ConnectionResetError, ConnectionRefusedError, OSError):
            return False

    def close(self, lock=False):
        if self.closed:
            return

        log.debug("Closing device...")
        self.closed = True
        if lock:
            event_bus.wait_for(EVENT_SPP_CLOSED)

    def _connect_socket(self):
        # noinspection PyUnresolvedReferences
        self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
                                    socket.BTPROTO_RFCOMM)
        self.socket.settimeout(2)
        self.socket.connect((self.address, port))

    def _mainloop(self):
        log.info("starting recv...")
        last_pkg = time.time()

        while not self.closed:
            result = self._do_recv()
            if result is None:
                break

            if result:
                last_pkg = time.time()

            if self.config.USE_SOCKET_SLEEP and time.time() - last_pkg > 5:
                self._sleep_start()
                event_bus.wait_for(EVENT_SPP_WAKE_UP)
                self._sleep_leave()

        log.info("Leaving recv...")
        self.socket.close()
        self.closed = True
        event_bus.invoke(EVENT_SPP_CLOSED)

    def _sleep_start(self):
        log.debug("No packages, going to sleep...")
        self.socket.close()
        self.sleep = True
        event_bus.timer(10, EVENT_SPP_WAKE_UP)

    def _sleep_leave(self):
        self.sleep = False
        self._connect_socket()
        event_bus.invoke(EVENT_SPP_ON_WAKE_UP)
        log.debug("Waked up...")
        self.on_wake_up()

    def _do_recv(self):
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
            return False
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            # Something bad happened, exiting...
            return None

        return True

    def _send_command(self, data, read=False):
        self.send(protocol_utils.build_spp_bytes(data))

        if read:
            t = time.time()
            event_bus.wait_for(EVENT_SPP_RECV, timeout=1)
            if time.time() - t > 0.9:
                log.warning("Too long read wait, maybe command is ignored")

    def send(self, data):
        if self.sleep:
            event_bus.invoke(EVENT_SPP_WAKE_UP)
            event_bus.wait_for(EVENT_SPP_ON_WAKE_UP, timeout=1)

        try:
            log.debug("send " + data.hex())
            self.socket.send(data)
        except ConnectionResetError:
            self.close()
            return

    def on_wake_up(self):
        raise Exception("Must be override")

    def on_init(self):
        raise Exception("Must be override")

    def on_package(self, pkg):
        raise Exception("Must be override")
