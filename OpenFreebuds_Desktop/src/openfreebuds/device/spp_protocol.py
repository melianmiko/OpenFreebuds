import logging
import queue
import socket
import threading
import time
from queue import Queue

import bluetooth

from openfreebuds import event_bus
from openfreebuds.device.base import BaseDevice
from openfreebuds.constants.events import EVENT_SPP_CLOSED, EVENT_SPP_RECV, EVENT_SPP_WAKE_UP, EVENT_SPP_ON_WAKE_UP

log = logging.getLogger("SPPDevice")
SLEEP_DELAY = 5
SLEEP_TIME = 20


class SppProtocolDevice(BaseDevice):
    SPP_SERVICE_UUID = ""

    def __init__(self, address):
        super().__init__()
        self.last_pkg = None
        self.address = address
        self.sleep = False
        self.socket = None

        self._send_queue = Queue()

    def connect(self):
        if self.closed:
            raise Exception("Can't reuse exiting device object")

        try:
            self._connect_socket()

            self._run_thread(self._thread_recv)
            self._run_thread(self._thread_send)
            self.on_init()

            return True
        except SocketConnectionError:
            log.exception("Can't create socket connection")
            self.close()
            return False

    def _run_thread(self, fnc):
        if self.config.SAFE_RUN_WRAPPER is None:
            threading.Thread(target=fnc).start()
        else:
            log.debug("Starting via safe wrapper")
            self.config.SAFE_RUN_WRAPPER(fnc, "SPPDevice", False)

    def request_interaction(self):
        try:
            self._connect_socket()
            time.sleep(1)

            self.socket.close()
            return True
        except SocketConnectionError:
            return False

    def close(self, lock=False):
        if self.closed:
            return

        if self.sleep:
            event_bus.invoke(EVENT_SPP_WAKE_UP)

        log.debug("Closing device...")
        self.closed = True
        if lock:
            event_bus.wait_for(EVENT_SPP_CLOSED)

    def _connect_socket(self):
        try:
            # noinspection PyUnresolvedReferences
            self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
                                        socket.BTPROTO_RFCOMM)
            self.socket.settimeout(2)

            service_data = bluetooth.find_service(address=self.address,
                                                  uuid=self.SPP_SERVICE_UUID)

            if len(service_data) < 1:
                raise ValueError("Service not found")

            self.socket.connect((service_data[0]["host"],
                                 service_data[0]["port"]))
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError, ValueError):
            raise SocketConnectionError()

    # noinspection PyBroadException
    def _thread_send(self):
        log.info("starting send thread...")
        data = b""
        while not self.closed:
            try:
                data = self._send_queue.get(timeout=2)
                log.debug("send " + data.hex())
                self.socket.send(data)
            except queue.Empty:
                pass
            except ConnectionResetError:
                self.close()
            except Exception:
                log.exception("Send exception, package={}".format(data.hex()))
        log.info("leaving send thread...")

    def _thread_recv(self):
        log.info("starting recv...")
        last_pkg = time.time()

        while not self.closed:
            result = self._do_recv()
            if result is None:
                break

            if result:
                last_pkg = time.time()

            if self.config.USE_SOCKET_SLEEP and time.time() - last_pkg > SLEEP_DELAY:
                self._sleep_start()
                event_bus.wait_for(EVENT_SPP_WAKE_UP, timeout=SLEEP_TIME)
                self._sleep_leave()

        log.info("Leaving recv...")
        self.socket.close()
        self.closed = True
        event_bus.invoke(EVENT_SPP_CLOSED)

    def _sleep_start(self):
        try:
            log.debug("No packages, going to sleep...")
            self.socket.close()
            self.sleep = True
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError):
            log.exception("Can't create socket connection")
            self.close()

    def _sleep_leave(self):
        try:
            self.sleep = False
            self._connect_socket()
            self.on_wake_up()
            log.debug("Waked up...")
            event_bus.invoke(EVENT_SPP_ON_WAKE_UP)
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError, ValueError):
            log.exception("Can't create socket connection")
            self.close()

    def _do_recv(self):
        try:
            byte = self.socket.recv(4)
            if byte[0:2] == b"Z\x00":
                length = byte[2]
                if length < 4:
                    self.socket.recv(length)
                else:
                    pkg = self.socket.recv(length)
                    self._process_package(pkg)
                    event_bus.invoke(EVENT_SPP_RECV)
        except (TimeoutError, socket.timeout):
            # Socket timed out, do nothing
            return False
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            # Something bad happened, exiting...
            return None

        return True

    def send(self, data: bytes):
        self._send_queue.put(data)

    def on_wake_up(self):
        raise Exception("Must be override")

    def on_init(self):
        raise Exception("Must be override")

    def on_package(self, pkg):
        raise Exception("Must be override")

    def _process_package(self, pkg):
        start = time.time()
        self.on_package(pkg)
        process_time = time.time() - start

        if process_time > 0.1:
            log.debug("Package processing took {}, too long".format(process_time))


class SocketConnectionError(Exception):
    pass
