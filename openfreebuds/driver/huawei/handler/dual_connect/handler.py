import asyncio
from typing import Optional

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.handler.dual_connect.constants import OfbHuaweiDualConnCommand
from openfreebuds.driver.huawei.handler.dual_connect.models import OfbHuaweiDualConnectRow
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiDualConnectHandler")


class OfbHuaweiDualConnectHandler(OfbDriverHandlerHuawei):
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
        self._pending_devices: dict[int, OfbHuaweiDualConnectRow] = {}
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
        self._pending_devices[dev_index] = OfbHuaweiDualConnectRow(package)

        is_ready = (self._devices_count == len(self._pending_devices.values())
                    or self.init_attempt == self.init_attempt_max - 1)

        if is_ready and self._on_ready:
            self._on_ready.set()

    async def set_property(self, group: str, payload: str, value: str):
        address, prop, *_ = *payload.split(":"), "", ""
        if prop == "auto_connect":
            cmd = OfbHuaweiDualConnCommand.ENABLE_AUTO if value == "true" else OfbHuaweiDualConnCommand.DISABLE_AUTO
            await self._exec_command(cmd, address)
        elif prop == "connected":
            cmd = OfbHuaweiDualConnCommand.CONNECT if value == "true" else OfbHuaweiDualConnCommand.DISCONNECT
            await self._exec_command(cmd, address)
        elif prop == "name" and value == "":
            await self._exec_command(OfbHuaweiDualConnCommand.UNPAIR, address)
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
