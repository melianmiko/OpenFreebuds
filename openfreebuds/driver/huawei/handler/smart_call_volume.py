import asyncio
import json

from openfreebuds.driver.huawei.constants import CMD_SMART_CALL_VOLUME_READ, CMD_SMART_CALL_VOLUME_WRITE
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiSmartCallVolumeHandler(OfbDriverHandlerHuawei):
    """
    Smart/adaptive call volume toggle.

    Huawei Audio Connect treats response value 0 as supported/off, 1 as
    supported/on, and every other value as unsupported.
    """

    handler_id = "smart_call_volume"
    commands = [CMD_SMART_CALL_VOLUME_READ, CMD_SMART_CALL_VOLUME_WRITE]
    init_attempt_max = 1
    properties = [
        ("sound", "smart_call_volume"),
    ]

    def __init__(self):
        self._supported = True

    async def on_init(self):
        try:
            resp = await self.driver.send_package(HuaweiSppPackage.read_rq(CMD_SMART_CALL_VOLUME_READ, [1]), timeout=2)
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            return

        if resp is not None:
            await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package.is_error_response():
            self._supported = False
            return False

        state = package.find_param(1)
        if len(state) != 1 or state[0] not in (0, 1):
            self._supported = False
            return False

        await self.driver.put_property("sound", "smart_call_volume", json.dumps(state[0] == 1))
        self._supported = True
        return True

    async def set_property(self, group: str, prop: str, value: str):
        if not self._supported:
            return

        enabled = value == "true" or value is True
        resp = await self.driver.send_package(
            HuaweiSppPackage.change_rq(CMD_SMART_CALL_VOLUME_WRITE, [(1, 1 if enabled else 0)]),
            timeout=3,
        )
        if resp is None or resp.is_error_response():
            if resp is not None:
                self._supported = False
            return

        if not await self.on_package(resp):
            await self.driver.put_property(group, prop, json.dumps(enabled))