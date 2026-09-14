import asyncio
import json

from openfreebuds.driver.huawei.constants import (
    CMD_BIG_VOLUME_NEW_READ,
    CMD_BIG_VOLUME_NEW_WRITE,
    CMD_BIG_VOLUME_READ,
    CMD_BIG_VOLUME_WRITE,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiBigVolumeHandler(OfbDriverHandlerHuawei):
    """
    Huawei big volume toggle.

    Newer devices first expose support through 2b88 param 2, then state through
    2b88 param 1. Older devices use 2b80/2b7f directly.
    """

    handler_id = "big_volume"
    commands = [
        CMD_BIG_VOLUME_READ,
        CMD_BIG_VOLUME_WRITE,
        CMD_BIG_VOLUME_NEW_READ,
        CMD_BIG_VOLUME_NEW_WRITE,
    ]
    properties = [
        ("sound", "big_volume"),
    ]

    def __init__(self):
        self._use_new_protocol: bool | None = None
        self._supported = True

    async def on_init(self):
        await self._query_protocol()
        await self._query_state()

    async def set_property(self, group: str, prop: str, value: str):
        if not self._supported:
            return

        enabled = value == "true" or value is True

        if self._use_new_protocol is None:
            await self._query_protocol()
        if not self._supported:
            return

        command = CMD_BIG_VOLUME_NEW_WRITE if self._use_new_protocol else CMD_BIG_VOLUME_WRITE
        resp = await self.driver.send_package(
            HuaweiSppPackage.change_rq(command, [(1, 1 if enabled else 0)]),
            timeout=3,
        )
        if resp is None or resp.is_error_response():
            if resp is not None:
                self._supported = False
            return

        if not await self.on_package(resp):
            await self.driver.put_property(group, prop, json.dumps(enabled))

    async def on_package(self, package: HuaweiSppPackage):
        if package.is_error_response():
            return False

        applied = False
        state = package.find_param(1)
        if len(state) == 1:
            await self.driver.put_property("sound", "big_volume", json.dumps(state[0] == 1))
            applied = True

        if package.command_id == CMD_BIG_VOLUME_NEW_READ:
            support = package.find_param(2)
            if len(support) == 1:
                self._use_new_protocol = support[0] == 1

        return applied

    async def _query_protocol(self):
        try:
            resp = await self.driver.send_package(
                HuaweiSppPackage.read_rq(CMD_BIG_VOLUME_NEW_READ, [2]),
                timeout=2,
            )
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            self._use_new_protocol = False
            return

        if resp is None:
            self._use_new_protocol = False
            return

        if resp.is_error_response():
            self._use_new_protocol = False
            return

        await self.on_package(resp)
        if self._use_new_protocol is None:
            self._use_new_protocol = False

    async def _query_state(self):
        command = CMD_BIG_VOLUME_NEW_READ if self._use_new_protocol else CMD_BIG_VOLUME_READ
        try:
            resp = await self.driver.send_package(HuaweiSppPackage.read_rq(command, [1]), timeout=2)
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            return

        if resp is None:
            return

        if resp.is_error_response():
            self._supported = False
            return

        applied = await self.on_package(resp)
        if not applied:
            self._supported = False