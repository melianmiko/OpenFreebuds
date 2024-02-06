from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


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

    def on_init(self):
        self.device.put_group("dev_name", {}, silent=True)
        self.device.put_group("dev_auto_connect", {}, silent=True)
        self.device.put_group("dev_connected", {}, silent=True)
        self.device.put_property("config", "preferred_device", "0" * 12)

        self.device.send_package(HuaweiSppPackage(b"\x2b\x31", [
            (1, b""),
        ]))
        self.device.send_package(HuaweiSppPackage(b"\x2b\x31", [
            (1, b""),
        ]))

    def on_package(self, package: HuaweiSppPackage):
        if package.command_id == b"\x2b\x36":
            return self.on_init()

        mac_addr = package.find_param(4).hex()
        if len(mac_addr) < 12:
            return
        is_connected = package.find_param(5)
        is_auto_connect = package.find_param(8)
        is_prior = package.find_param(7)
        name = package.find_param(9).decode("utf8", "ignore")

        self.device.put_property("dev_name", mac_addr, name)
        self.device.put_property("dev_auto_connect", mac_addr, is_auto_connect[0] != 0)
        self.device.put_property("dev_connected", mac_addr, is_connected[0] != 0)

        if is_prior[0] == 1:
            self.device.put_property("config", "preferred_device", mac_addr)

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
