import asyncio
import json
from typing import Optional

from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("FbHuaweiDualConnectHandler")


class _CommandID:
    CONNECT = 1
    DISCONNECT = 2
    UNPAIR = 3
    ENABLE_AUTO = 4
    DISABLE_AUTO = 5


class _PendingDeviceRow:
    def __init__(self, package: HuaweiSppPackage):
        self.name = package.find_param(9).decode("utf8", "ignore")
        self.auto_connect = package.find_param(8)[0] == 1
        self.preferred = package.find_param(7)[0] == 1
        self.mac = package.find_param(4).hex()

        conn_state = package.find_param(5)[0]
        self.connected = conn_state > 0
        self.playing = conn_state == 9

    def __str__(self):
        return json.dumps({
            "name": self.name,
            "auto_connect": self.auto_connect,
            "preferred": self.preferred,
            "connected": self.connected,
            "playing": self.playing,
        })


class FbHuaweiDualConnectHandler(FbDriverHandlerHuawei):
    handler_id = "dual_connect_devices"
    properties = [
        ("dual_connect_devices", ""),
        ("config", "preferred_device"),
    ]
    commands = [b"\x2b\x31", b"\x2b\x36"]
    ignore_commands = [b"\x2b\x32", b"\x2b\x33"]
    init_timeout = 1
    init_attempt_max = 6

    def __init__(self):
        super().__init__()

        self._on_ready: Optional[asyncio.Event] = None
        self._pending_devices: dict[int, _PendingDeviceRow] = {}
        self._devices_count: int = 999
        self._task_re_init: Optional[asyncio.Task] = None

    async def on_init(self):
        if self._on_ready is not None:
            return

        if self.init_attempt == 0:
            self._pending_devices = {}
            self._devices_count = 999

        # Ask for enumerating
        try:
            self._on_ready = asyncio.Event()
            await self.driver.send_package(HuaweiSppPackage(b"\x2b\x31", [
                (1, b""),
            ]))
            # log.info("Start enumerating devices...")
            await self._on_ready.wait()
        finally:
            self._on_ready = None

        # Process new records
        log.info("All DC devices listed, processing...")
        await self._process_pending_devices()

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id == b"\x2b\x36":
            self._task_re_init = asyncio.create_task(self.init())
            return

        mac_addr = package.find_param(4).hex()
        if len(mac_addr) < 12:
            return

        dev_index = int.from_bytes(package.find_param(3), byteorder="big", signed=True)
        self._devices_count = int.from_bytes(package.find_param(2), byteorder="big", signed=True)
        self._pending_devices[dev_index] = _PendingDeviceRow(package)

        is_ready = (self._devices_count == len(self._pending_devices.values())
                    or self.init_attempt == self.init_attempt_max - 1)

        if is_ready and self._on_ready:
            self._on_ready.set()

    async def set_property(self, group: str, payload: str, value: str):
        address, prop, *_ = *payload.split(":"), "", ""
        if prop == "auto_connect":
            cmd = _CommandID.ENABLE_AUTO if value == "true" else _CommandID.DISABLE_AUTO
            await self._exec_command(cmd, address)
        elif prop == "connected":
            cmd = _CommandID.CONNECT if value == "true" else _CommandID.DISCONNECT
            await self._exec_command(cmd, address)
        elif prop == "name" and value == "":
            await self._exec_command(_CommandID.UNPAIR, address)
        elif payload == "preferred_device":
            await self._set_preferred(value)
        elif payload == "refresh":
            pass
        else:
            log.warning(f"Unknown request-prop {group}//{payload} = {value}")
            return

        self._task_re_init = asyncio.create_task(self.init())

    async def _process_pending_devices(self):
        devices = {}
        preferred = "0" * 12

        for index in range(self._devices_count):
            if index not in self._pending_devices:
                continue
            device = self._pending_devices[index]
            devices[device.mac] = str(device)
            if device.preferred:
                preferred = device.mac

        await self.driver.put_property("dual_connect_devices", None, devices)
        await self.driver.put_property("config", "preferred_device", preferred)

    async def _set_preferred(self, mac_addr):
        return await self.driver.send_package(HuaweiSppPackage.change_rq_nowait(b"\x2b\x32", [
            (1, bytes.fromhex(mac_addr)),
        ]))

    async def _exec_command(self, cmd_id: int, address: str):
        log.debug(f"Executing DC manage command {cmd_id} for {address}")
        return await self.driver.send_package(HuaweiSppPackage.change_rq_nowait(b"\x2b\x33", [
            (cmd_id, bytes.fromhex(address)),
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
            (1, 1 if value == "true" else 0),
        ])
        await self.driver.send_package(pkg)
        await self.init()

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(1)

        if len(value) == 1:
            value = int(value[0])
            await self.driver.put_property("config", "dual_connect", "true" if value == 1 else "false")
