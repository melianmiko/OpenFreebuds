from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class DualConnectDevicesHandler(HuaweiSppHandler):
    """
    EXPERIMENTAL "Device center" implementation
    """
    handler_id = "dual_connect_devices"
    handle_props = (
        ("dev_name", ""),
        ("dev_auto_connect", ""),
        ("dev_connected", ""),
        ("config", "preferred_device"),
    )
    handle_commands = (
        b"\x2b\x31",
    )
    ignore_commands = (
        b"\x2b\x32",
        b"\x2b\x33",
    )

    def on_init(self):
        self.device.put_group("dev_name", {}, silent=True)
        self.device.put_group("dev_auto_connect", {}, silent=True)
        self.device.put_group("dev_connected", {}, silent=True)
        self.device.put_property("config", "preferred_device", "auto")

        self.device.send_package(HuaweiSppPackage(b"\x2b\x31", [
            (1, b""),
        ]))

    def on_package(self, package: HuaweiSppPackage):
        print(package, flush=True)

        mac_addr = package.find_param(4).hex()
        if len(mac_addr) < 12:
            return
        is_connected = package.find_param(3)  # experiment
        is_auto_connect = package.find_param(6)  # experiment
        is_prior = package.find_param(7)
        name = package.find_param(9).decode("utf8")

        self.device.put_property("dev_name", mac_addr, name, silent=True)
        self.device.put_property("dev_auto_connect", mac_addr, is_auto_connect == 1, silent=True)
        self.device.put_property("dev_connected", mac_addr, is_connected == 1)

        if is_prior:
            self.device.put_property("config", "preferred_device", mac_addr)

    def on_prop_changed(self, group: str, prop: str, value):
        if group == "dev_auto_connect":
            self._set_auto_connect(prop, value)
        elif group == "dev_connected":
            self._set_connected(prop, value)
        elif group == "device_name" and value == "":
            self._unpair(prop)
        self.on_init()

    def _set_auto_connect(self, mac_addr: str, value: bool):
        p_type = 6 if value else 5
        self.device.send_package(b"\x2b\x33", [
            (p_type, bytes.fromhex(mac_addr)),
        ])

    def _set_connected(self, mac_addr: str, value: bool):
        p_type = 1 if value else 2
        self.device.send_package(b"\x2b\x33", [
            (p_type, bytes.fromhex(mac_addr)),
        ])

    def _unpair(self, mac_addr: str):
        self.device.send_package(b"\x2b\x33", [
            (3, bytes.fromhex(mac_addr)),
        ])
