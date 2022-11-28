import logging
import queue
import socket
import threading
import time
from queue import Queue

import bluetooth

from openfreebuds import event_bus
from openfreebuds.device.base import BaseDevice
from openfreebuds.constants.events import EVENT_SPP_CLOSED, EVENT_SPP_RECV

log = logging.getLogger("SPPDevice")
SLEEP_DELAY = 5
SLEEP_TIME = 20


class SppProtocolDevice(BaseDevice):
    SPP_SERVICE_UUID = ""

    def __init__(self, address):
        super().__init__()
        self.closed = False
        self.last_pkg = None
        self.address = address
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

            try:
                service_data = bluetooth.find_service(address=self.address,
                                                      uuid=self.SPP_SERVICE_UUID)
                assert len(service_data) > 0
                host = service_data[0]['host']
                port = service_data[0]['port']
                log.info(f"Found serial port {host}:{port} from UUID")
            except (AssertionError, NameError) as e:
                log.error(f"Can't fetch service info from device, err: {e}")
                log.warning("Can't fetch serial port info from device, attempt to use "
                            "fallback port 16. This is issue of pybluez2, to fix uninstall it,"
                            "then build and install pybluez from one of latest commits")
                host = self.address
                port = 16

            self.socket.connect((host, port))
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

        while not self.closed:
            result = self._do_recv()
            if result is None:
                break

        log.info("Leaving recv...")
        self.socket.close()
        self.closed = True
        event_bus.invoke(EVENT_SPP_CLOSED)

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
        log.debug("recv " + pkg.hex())
        start = time.time()
        self.on_package(pkg)
        process_time = time.time() - start

        if process_time > 0.1:
            log.debug("Package processing took {}, too long".format(process_time))


class SocketConnectionError(Exception):
    pass
