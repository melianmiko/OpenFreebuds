import asyncio

from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("FbHuaweiDualConnectHandler")


class _PendingDeviceRow:
    def __init__(self, name: str, mac: str, connected: bool, auto_connect: bool, primary: bool):
        self.name = name
        self.mac = mac
        self.connected = connected
        self.auto_connected = auto_connect
        self.primary = primary


class FbHuaweiDualConnectHandler(FbDriverHandlerHuawei):
    handler_id = "dual_connect_devices"
    properties = [
        ("dev_name", ""),
        ("dev_auto_connect", ""),
        ("dev_connected", ""),
        ("config", "preferred_device"),
        ("config", "refresh_devices"),
    ]
    commands = [b"\x2b\x31", b"\x2b\x36"]
    ignore_commands = [b"\x2b\x32", b"\x2b\x33"]

    def __init__(self):
        super().__init__()

        self._on_all_devices_ready: asyncio.Event = asyncio.Event()
        self._pending_devices: dict[int, _PendingDeviceRow] = {}

    async def on_init(self):
        async with asyncio.timeout(3):
            self._pending_devices = {}
            self._on_all_devices_ready.clear()

            # Ask for enumerating
            log.info("Start enumerating devices...")
            await self.driver.send_package(HuaweiSppPackage(b"\x2b\x31", [
                (1, b""),
            ]))
            await self._on_all_devices_ready.wait()

            # Process new records
            log.info("All DC devices listed, processing...")
            await self._process_pending_devices()

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id == b"\x2b\x36":
            return await self.on_init()

        mac_addr = package.find_param(4).hex()
        if len(mac_addr) < 12:
            return

        dev_count = int.from_bytes(package.find_param(2), byteorder="big", signed=True)
        dev_index = int.from_bytes(package.find_param(3), byteorder="big", signed=True)
        self._pending_devices[dev_index] = _PendingDeviceRow(mac=mac_addr,
                                                             name=package.find_param(9).decode("utf8", "ignore"),
                                                             connected=package.find_param(5)[0] == 1,
                                                             auto_connect=package.find_param(8)[0] == 1,
                                                             primary=package.find_param(7)[0] == 1)

        if dev_count == len(self._pending_devices.values()):
            self._on_all_devices_ready.set()

    async def set_property(self, group: str, prop: str, value: str):
        if group == "dev_auto_connect":
            resp = await self._set_auto_connect(prop, value == "true")
        elif group == "dev_connected":
            resp = await self._set_connected(prop, value == "true")
        elif group == "dev_name" and value == "":
            resp = await self._unpair(prop)
        elif prop == "preferred_device":
            resp = await self._set_preferred(value)
        else:
            resp = await self.on_init()

        if resp is not None and resp.find_param(2)[0] == 0:
            await self.driver.put_property(group, prop, value)

    async def _process_pending_devices(self):
        names, auto_connect, connected = {}, {}, {}
        preferred = "0" * 12

        for device in self._pending_devices.values():
            names[device.mac] = device.name
            auto_connect[device.mac] = device.auto_connected
            connected[device.mac] = device.connected
            if device.primary:
                preferred = device.mac

        await self.driver.put_property("dev_name", None, names)
        await self.driver.put_property("dev_auto_connect", None, auto_connect)
        await self.driver.put_property("dev_connected", None, connected)
        await self.driver.put_property("config", "preferred_device", preferred)

    async def _set_preferred(self, mac_addr):
        return await self.driver.send_package(HuaweiSppPackage.change_rq(b"\x2b\x32", [
            (1, bytes.fromhex(mac_addr)),
        ]))

    async def _set_auto_connect(self, mac_addr: str, value: bool):
        p_type = 4 if value else 5
        return await self.driver.send_package(HuaweiSppPackage.change_rq(b"\x2b\x33", [
            (p_type, bytes.fromhex(mac_addr)),
        ]))

    async def _set_connected(self, mac_addr: str, value: bool):
        p_type = 1 if value else 2
        return await self.driver.send_package(HuaweiSppPackage.change_rq(b"\x2b\x33", [
            (p_type, bytes.fromhex(mac_addr)),
        ]))

    async def _unpair(self, mac_addr: str):
        return await self.driver.send_package(HuaweiSppPackage.change_rq(b"\x2b\x33", [
            (3, bytes.fromhex(mac_addr)),
        ]))


class FbHuaweiDualConnectToggleHandler(FbDriverHandlerHuawei):
    """
    Enable/disable multi-device support (pro 3, 5i)
    """
    handler_id = "dual_connect_toggle"
    commands = [b"\x2b\x2f"]
    ignore_commands = [b"\x2b\x2e"]
    properties = [
        ("config", "dual_connect"),
    ]

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\x2f", [1]))
        await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
        pkg = HuaweiSppPackage.change_rq(b"\x2b\x2e", [
            (1, 1 if value else 0),
        ])
        resp = await self.driver.send_package(pkg)
        if resp.find_param(2)[0] == 0:
            await self.driver.put_property(group, prop, value)

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(1)

        if len(value) == 1:
            value = int(value[0])
            await self.driver.put_property("config", "dual_connect", value == 1)
