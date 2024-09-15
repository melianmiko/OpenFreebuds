import asyncio
import json
from typing import Optional

from openfreebuds.driver.huawei.constants import CMD_DUAL_CONNECT_ENUMERATE, CMD_DUAL_CONNECT_ENABLED_WRITE, \
    CMD_DUAL_CONNECT_EXECUTE, CMD_DUAL_CONNECT_PREFERRED_WRITE, CMD_DUAL_CONNECT_ENABLED_READ, \
    CMD_DUAL_CONNECT_CHANGE_EVENT
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.handler.dual_connect.constants import OfbHuaweiDualConnCommand
from openfreebuds.driver.huawei.handler.dual_connect.models import OfbHuaweiDualConnectRow
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiDualConnectHandler")


class OfbHuaweiDualConnectHandler(OfbDriverHandlerHuawei):
    handler_id = "dual_connect"
    commands = [
        CMD_DUAL_CONNECT_ENUMERATE,
        CMD_DUAL_CONNECT_CHANGE_EVENT,
        CMD_DUAL_CONNECT_ENABLED_READ
    ]
    ignore_commands = [
        CMD_DUAL_CONNECT_PREFERRED_WRITE,
        CMD_DUAL_CONNECT_EXECUTE,
        CMD_DUAL_CONNECT_ENABLED_WRITE
    ]
    init_timeout = 1
    init_attempt_max = 6
    properties = [
        ("dual_connect", ""),
    ]

    def __init__(self, w_auto_connect: bool = True):
        super().__init__()

        self.w_auto_connect = w_auto_connect

        self._on_ready: Optional[asyncio.Event] = None
        self._pending_devices: dict[int, OfbHuaweiDualConnectRow] = {}
        self._devices_count: int = 999
        self._task_re_init: Optional[asyncio.Task] = None

    async def on_init(self):
        if self._on_ready is not None:
            return

        if self.init_attempt == 0:
            await self._init_toggle()
            self._pending_devices = {}
            self._devices_count = 999

        # Ask for enumerating
        try:
            self._on_ready = asyncio.Event()
            await self.driver.send_package(HuaweiSppPackage(CMD_DUAL_CONNECT_ENUMERATE, [
                (1, b""),
            ]))
            # log.info("Start enumerating devices...")
            await self._on_ready.wait()
        finally:
            self._on_ready = None

        # Process new records
        log.info("All DC devices listed, processing...")
        await self._process_pending_devices()

    async def _init_toggle(self):
        resp = await self.driver.send_package(
            HuaweiSppPackage.read_rq(CMD_DUAL_CONNECT_ENABLED_READ, [1])
        )
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package.command_id == CMD_DUAL_CONNECT_CHANGE_EVENT:
            self._task_re_init = asyncio.create_task(self.init())
            return
        elif package.command_id == CMD_DUAL_CONNECT_ENABLED_READ:
            value = package.find_param(1)

            if len(value) == 1:
                value = int(value[0])
                await self.driver.put_property("dual_connect", "enabled", "true" if value == 1 else "false")
            return
        else:
            mac_addr = package.find_param(4).hex()
            if len(mac_addr) < 12:
                return

            dev_index = int.from_bytes(package.find_param(3), byteorder="big", signed=True)
            self._devices_count = int.from_bytes(package.find_param(2), byteorder="big", signed=True)
            self._pending_devices[dev_index] = OfbHuaweiDualConnectRow(package, self.w_auto_connect)

            is_ready = (self._devices_count == len(self._pending_devices.values())
                        or self.init_attempt == self.init_attempt_max - 1)

            if is_ready and self._on_ready:
                self._on_ready.set()

    async def set_property(self, group: str, payload: str, value: str):
        address, prop, *_ = *payload.split(":"), "", ""

        if payload == "enabled":
            # Assign global toggle
            await self._toggle_enabled(value)
        elif payload == "preferred_device":
            # Assign preferred device
            await self._set_preferred(value)
        elif payload == "refresh":
            # Refresh command
            pass
        elif prop == "auto_connect":
            # Toggle auto-connect command
            cmd = OfbHuaweiDualConnCommand.ENABLE_AUTO if value == "true" else OfbHuaweiDualConnCommand.DISABLE_AUTO
            await self._exec_command(cmd, address)
        elif prop == "connected":
            # Toggle connected command
            cmd = OfbHuaweiDualConnCommand.CONNECT if value == "true" else OfbHuaweiDualConnCommand.DISCONNECT
            await self._exec_command(cmd, address)
        elif prop == "name" and value == "":
            # Unpair command
            await self._exec_command(OfbHuaweiDualConnCommand.UNPAIR, address)
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
            devices[device.mac] = device.to_dict()
            if device.preferred:
                preferred = device.mac

        await self.driver.put_property("dual_connect", "devices", json.dumps(devices))
        await self.driver.put_property("dual_connect", "preferred_device", preferred)

    async def _set_preferred(self, mac_addr):
        return await self.driver.send_package(
            HuaweiSppPackage.change_rq_nowait(CMD_DUAL_CONNECT_PREFERRED_WRITE, [
                (1, bytes.fromhex(mac_addr)),
            ])
        )

    async def _exec_command(self, cmd_id: int, address: str):
        log.debug(f"Executing DC manage command {cmd_id} for {address}")
        return await self.driver.send_package(
            HuaweiSppPackage.change_rq_nowait(CMD_DUAL_CONNECT_EXECUTE, [
                (cmd_id, bytes.fromhex(address)),
            ])
        )

    async def _toggle_enabled(self, value: str):
        pkg = HuaweiSppPackage.change_rq(CMD_DUAL_CONNECT_ENABLED_WRITE, [
            (1, 1 if value == "true" else 0),
        ])
        await self.driver.send_package(pkg)
        await self._init_toggle()
