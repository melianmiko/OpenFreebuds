import time

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.logger import create_log
from openfreebuds_applet.utils import async_with_ui

log = create_log("HuaweiHandlers")


class PendingDeviceRow:
    def __init__(self, name: str, mac: str, connected: bool, auto_connect: bool, primary: bool):
        self.name = name
        self.mac = mac
        self.connected = connected
        self.auto_connected = auto_connect
        self.primary = primary


class DualConnectDevicesHandler(HuaweiSppHandler):
    """
    EXPERIMENTAL "Device center" implementation
    """
    handler_id = "dual_connect_devices"
    handle_props = [
        ("dev_name", ""),
        ("dev_auto_connect", ""),
        ("dev_connected", ""),
        ("config", "preferred_device"),
        ("config", "refresh_devices"),
    ]
    handle_commands = (
        b"\x2b\x31",
        b"\x2b\x36",
    )
    ignore_commands = (
        b"\x2b\x32",
        b"\x2b\x33",
    )

    def __init__(self):
        self.pending_devices = {}  # type: dict[int, PendingDeviceRow]
        self.pending_dropped = False

    @async_with_ui("DualConnectDevicesEnumerate")
    def on_init(self):
        log.info("Start dual-connect device enumeration...")
        while True:
            self.device.put_group("dev_name", {}, silent=True)
            self.device.put_group("dev_auto_connect", {}, silent=True)
            self.device.put_group("dev_connected", {}, silent=True)
            self.device.put_property("config", "preferred_device", "0" * 12)
            self.pending_dropped = False
            self.pending_devices = {}

            self.device.send_package(HuaweiSppPackage(b"\x2b\x31", [
                (1, b""),
            ]))

            time.sleep(10)
            if self.pending_dropped:
                return
            log.info("Timed out waiting device enumeration, retry...")

    def on_package(self, package: HuaweiSppPackage):
        if package.command_id == b"\x2b\x36":
            return self.on_init()

        mac_addr = package.find_param(4).hex()
        if len(mac_addr) < 12:
            return

        dev_count = int.from_bytes(package.find_param(2), byteorder="big", signed=True)
        dev_index = int.from_bytes(package.find_param(3), byteorder="big", signed=True)
        self.pending_devices[dev_index] = PendingDeviceRow(mac=mac_addr,
                                                           name=package.find_param(9).decode("utf8", "ignore"),
                                                           connected=package.find_param(5)[0] == 1,
                                                           auto_connect=package.find_param(8)[0] == 1,
                                                           primary=package.find_param(7)[0] == 1)

        if dev_count == len(self.pending_devices.values()):
            self._process_pending_devices()

    def _process_pending_devices(self):
        log.info("All devices are received, processing")
        self.pending_dropped = True

        names, auto_connect, connected = {}, {}, {}
        preferred = "0" * 12

        for device in self.pending_devices.values():
            names[device.mac] = device.name
            auto_connect[device.mac] = device.auto_connected
            connected[device.mac] = device.connected
            if device.primary:
                preferred = device.mac

        self.device.put_group("dev_name", names, silent=True)
        self.device.put_group("dev_auto_connect", auto_connect, silent=True)
        self.device.put_group("dev_connected", connected, silent=True)
        self.device.put_property("config", "preferred_device", preferred)

    def on_prop_changed(self, group: str, prop: str, value):
        if group == "dev_auto_connect":
            self._set_auto_connect(prop, value)
        elif group == "dev_connected":
            self._set_connected(prop, value)
        elif group == "dev_name" and value == "":
            self._unpair(prop)
        elif prop == "preferred_device":
            self._set_preferred(value)
        elif prop == "refresh_devices":
            self.on_init()
        self.on_init()

    def _set_preferred(self, mac_addr):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x32", [
            (1, bytes.fromhex(mac_addr)),
        ]))

    def _set_auto_connect(self, mac_addr: str, value: bool):
        p_type = 4 if value else 5
        self.device.send_package(HuaweiSppPackage(b"\x2b\x33", [
            (p_type, bytes.fromhex(mac_addr)),
        ]))

    def _set_connected(self, mac_addr: str, value: bool):
        p_type = 1 if value else 2
        self.device.send_package(HuaweiSppPackage(b"\x2b\x33", [
            (p_type, bytes.fromhex(mac_addr)),
        ]))

    def _unpair(self, mac_addr: str):
        self.device.send_package(HuaweiSppPackage(b"\x2b\x33", [
            (3, bytes.fromhex(mac_addr)),
        ]))
