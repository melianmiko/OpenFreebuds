import logging
import time

from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_SPP_RECV
from openfreebuds.device.generic.base import with_no_prop_changed_event
from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.device.huawei.interfaces.spp_device import HuaweiSppDevice

log = logging.getLogger("GenericHuaweiSppDevice")


class IgnoreHandler(HuaweiSppHandler):
    def on_package(self, package: HuaweiSppPackage):
        pass


class GenericHuaweiSppDevice(HuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)

        self.spp_service_uuid = "00001101-0000-1000-8000-00805f9b34fb"
        self.spp_fallback_port = 16

        self.handlers: list[HuaweiSppHandler] = []

        self._on_prop_change: dict[str, HuaweiSppHandler] = {}
        self._on_package: dict[bytes, HuaweiSppHandler] = {}
        self._ignore_handler = IgnoreHandler()

    @with_no_prop_changed_event
    def on_init(self):
        # Bind all handlers
        for handler in self.handlers:
            handler.on_device_ready(self)

            # Add to handlers hashtable
            for group, name in handler.handle_props:
                if f"{group}__{name}" in self._on_prop_change:
                    log.info(f"Conflicting prop handlers of {group}, {name}")
                self._on_prop_change[f"{group}__{name}"] = handler

            for command_id in handler.handle_commands:
                if command_id in self._on_package:
                    log.info(f"Conflicting command handlers of {command_id.hex()}")
                self._on_package[command_id] = handler

            for command_id in handler.ignore_commands:
                self._on_package[command_id] = self._ignore_handler

            handler.on_init()

    def send_package(self, pkg: HuaweiSppPackage, read=False):
        log.debug(f"send {pkg}")
        self.send(pkg.to_bytes())
        if read:
            t = time.time()
            event_bus.wait_for(EVENT_SPP_RECV, timeout=1)
            if time.time() - t > 0.9:
                log.warning("Too long read wait, maybe command is ignored")

    def on_set_property(self, group: str, prop: str, value):
        tag = f"{group}__{prop}"

        if tag not in self._on_prop_change:
            raise ValueError("This property can't be changed")

        self._on_prop_change[tag].on_prop_changed(group, prop, value)

    # noinspection PyBroadException
    def on_package(self, pkg: bytes):
        try:
            pkg = HuaweiSppPackage.from_bytes(pkg)
            log.debug(f"recv {pkg}")
        except Exception:
            log.exception(f"Got non-parsable package {pkg.hex()}, ignoring")
            return

        if pkg.command_id in self._on_package:
            self._on_package[pkg.command_id].on_package(pkg)
        else:
            log.debug(f"Got unsupported package\n{str(pkg)}")

    def do_socket_read(self):
        try:
            heading = self.socket.recv(4)
            if heading[0:2] == b"Z\x00":
                length = heading[2]
                if length < 4:
                    self.socket.recv(length)
                else:
                    pkg = heading + self.socket.recv(length)
                    self._process_package(pkg)
                    event_bus.invoke(EVENT_SPP_RECV)
        except TimeoutError:
            # Socket timed out, do nothing
            return False
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            # Something bad happened, exiting...
            return None

        return True

    def _process_package(self, pkg: bytes):
        start = time.time()
        self.on_package(pkg)
        process_time = time.time() - start

        if process_time > 0.1:
            log.debug("Package processing took {}, too long".format(process_time))
