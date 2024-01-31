import queue
import socket
import threading
import time
from queue import Queue

from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_SPP_CLOSED
from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.logger import create_log

log = create_log("GenericSPPDevice")
SLEEP_DELAY = 5
SLEEP_TIME = 20


class GenericSppDevice(BaseDevice):
    def __init__(self, address):
        super().__init__(address)
        self.spp_service_uuid = ""
        self.spp_fallback_port = 1
        self.spp_connect_sleep = 0

        self.closed = False
        self.last_pkg = None
        self.address = address
        self.socket = None

        self._send_queue = Queue()
        self._handle_queue = Queue()

    def connect(self):
        if self.closed:
            raise Exception("Can't reuse exiting device object")

        try:
            self._connect_socket()

            self._run_thread(self._thread_recv)
            self._run_thread(self._thread_send)
            self._run_thread(self._thread_handle)
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

            time.sleep(self.spp_connect_sleep)

            try:
                import bluetooth
                service_data = bluetooth.find_service(address=self.address,
                                                      uuid=self.spp_service_uuid)
                assert len(service_data) > 0
                host = service_data[0]['host']
                port = service_data[0]['port']
                log.info(f"Found serial port {host}:{port} from UUID")
            except (AssertionError, NameError, ImportError) as e:
                log.error(f"\n\nCan't fetch service info from device, err: {e}\n"
                          "Looks like pybluez didn't installed or didn't work as expected.\n"
                          "Using fallback port number 16\n  ")
                host = self.address
                port = self.spp_fallback_port

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
                # log.debug("send " + data.hex())
                self.socket.send(data)
            except queue.Empty:
                pass
            except ConnectionResetError:
                self.close()
            except Exception:
                log.exception("Send exception, package={}".format(data.hex()))
        log.info("leaving send thread...")

    def _thread_handle(self):
        log.info("starting handle...")

        while not self.closed:
            try:
                data = self._handle_queue.get(timeout=2)
                self.do_data_handle(data)
            except queue.Empty:
                pass

        log.info("Leaving handle...")

    def _thread_recv(self):
        log.info("starting recv...")

        while not self.closed:
            result = self.do_socket_read()
            if result is None:
                break

        log.info("Leaving recv...")
        self.socket.close()
        self.closed = True
        event_bus.invoke(EVENT_SPP_CLOSED)

    def send(self, data: bytes):
        self._send_queue.put(data)

    def do_socket_read(self):
        raise Exception("Must be overriden")

    def do_data_handle(self, data: bytes):
        raise Exception("Must be overriden")

    def on_init(self):
        raise Exception("Must be override")


class SocketConnectionError(Exception):
    pass
