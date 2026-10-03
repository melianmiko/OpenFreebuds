import asyncio
import json

from openfreebuds.driver.huawei.constants import CMD_HEADSET_SOUND_STATE_READ, CMD_HEADSET_SOUND_STATE_WRITE
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiFindDeviceHandler(OfbDriverHandlerHuawei):
    """
    Earbud sound locator used by Huawei's Find my device screen.
    """

    handler_id = "find_device"
    commands = [CMD_HEADSET_SOUND_STATE_READ, CMD_HEADSET_SOUND_STATE_WRITE]
    properties = [
        ("find_device", "left"),
        ("find_device", "right"),
    ]

    _SIDE_TO_PROP = {
        0: "left",
        1: "right",
    }
    _PROP_TO_SIDE = {value: key for key, value in _SIDE_TO_PROP.items()}

    init_timeout = 5
    init_attempt_max = 1

    async def on_init(self):
        for side in self._SIDE_TO_PROP:
            await self._read_side(side)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None or package.is_error_response():
            return
        if package.command_id not in self.commands:
            return

        state = package.find_param(2)
        if len(state) != 2:
            return

        side = state[0]
        prop = self._SIDE_TO_PROP.get(side)
        if prop is None:
            return

        await self.driver.put_property("find_device", prop, json.dumps(state[1] == 0))

    async def set_property(self, group: str, prop: str, value):
        if prop not in self._PROP_TO_SIDE:
            return

        side = self._PROP_TO_SIDE[prop]
        enabled = value is True or value == "true"
        sound_state = 0 if enabled else 1
        pkg = HuaweiSppPackage.change_rq(CMD_HEADSET_SOUND_STATE_WRITE, [(1, bytes([side, sound_state]))])
        try:
            resp = await self.driver.send_package(
                pkg,
                timeout=3,
                response_matcher=lambda package: self._matches_side(package, side),
            )
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            await self._read_side(side)
            return

        if resp is None or resp.is_error_response():
            return

        await self._read_side(side)

    async def _read_side(self, side: int):
        try:
            resp = await self.driver.send_package(
                HuaweiSppPackage(CMD_HEADSET_SOUND_STATE_READ, [(1, side)], resp=CMD_HEADSET_SOUND_STATE_READ),
                timeout=2,
                response_matcher=lambda package, expected_side=side: self._matches_side(package, expected_side),
            )
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            return

        if resp is not None:
            await self.on_package(resp)

    @staticmethod
    def _matches_side(package: HuaweiSppPackage, side: int) -> bool:
        if package.is_error_response():
            return True
        state = package.find_param(2)
        return len(state) == 2 and state[0] == side