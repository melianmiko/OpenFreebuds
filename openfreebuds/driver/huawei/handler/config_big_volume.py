import json

from openfreebuds.driver.huawei.constants import (
    CMD_BIG_VOLUME_LEGACY_QUERY,
    CMD_BIG_VOLUME_LEGACY_WRITE,
    CMD_BIG_VOLUME_QUERY,
    CMD_BIG_VOLUME_WRITE,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiBigVolumeHandler")

# Official BigVolumeRepository payloads:
#   query new support  2b 88 02 00 -> 2b 88 02 01 <0/1>
#   query new state    2b 88 01 00 -> 2b 88 01 01 <0/1>
#   write new state    2b 87 01 01 <0/1>
#   query legacy state 2b 80 01 00 -> 2b 80 01 01 <0/1>
#   write legacy state 2b 7f 01 01 <0/1>
_PARAM_STATE = 1
_PARAM_NEW_SUPPORT = 2


def _build_new_support_rq():
    return HuaweiSppPackage.change_rq(CMD_BIG_VOLUME_QUERY, [
        (_PARAM_NEW_SUPPORT, b""),
    ])


def _build_new_state_rq():
    return HuaweiSppPackage.change_rq(CMD_BIG_VOLUME_QUERY, [
        (_PARAM_STATE, b""),
    ])


def _build_legacy_state_rq():
    return HuaweiSppPackage.change_rq(CMD_BIG_VOLUME_LEGACY_QUERY, [
        (_PARAM_STATE, b""),
    ])


def _build_set_rq(command: bytes, enabled: bool):
    return HuaweiSppPackage.change_rq(command, [
        (_PARAM_STATE, 1 if enabled else 0),
    ])


class OfbHuaweiBigVolumeHandler(OfbDriverHandlerHuawei):
    """Noisy-environment media volume boost (official tag big_volume_new).

    The official app first probes the new 0x2B88 protocol, then falls back to
    the legacy 0x2B80 protocol used by the first-generation Eyewear. Runtime
    support is decided by the device response, so this handler is safe to
    mount on models whose config merely declares the feature.
    """

    handler_id = "config_big_volume"
    commands = [
        CMD_BIG_VOLUME_QUERY,
        CMD_BIG_VOLUME_WRITE,
        CMD_BIG_VOLUME_LEGACY_QUERY,
        CMD_BIG_VOLUME_LEGACY_WRITE,
    ]
    init_timeout = 1
    init_attempt_max = 2
    properties = [
        ("sound", "big_volume"),
        ("sound", "big_volume_supported"),
    ]

    def __init__(self):
        self.supported: bool = False
        self.use_new: bool = False
        self._new_support_seen: bool = False

    async def on_init(self):
        self.supported = False
        self.use_new = False
        self._new_support_seen = False

        resp = await self.driver.send_package(_build_new_support_rq())
        if resp is not None:
            await self.on_package(resp)

        if not self._new_support_seen:
            await self._read_legacy_state()
            return

        if self.use_new:
            resp = await self.driver.send_package(_build_new_state_rq())
            if resp is not None:
                await self.on_package(resp)
            if self.supported:
                return

        await self._read_legacy_state()

    async def _read_legacy_state(self):
        resp = await self.driver.send_package(_build_legacy_state_rq())
        if resp is None:
            await self.driver.put_property("sound", "big_volume_supported", "false")
            return
        await self.on_package(resp)

    async def _update_state(self, enabled: bool):
        self.supported = True
        await self.driver.put_property("sound", None, {
            "big_volume_supported": "true",
            "big_volume": json.dumps(enabled),
        }, extend_group=True)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None:
            return

        if package.command_id == CMD_BIG_VOLUME_QUERY:
            support = package.find_param(_PARAM_NEW_SUPPORT)
            if len(support) == 1:
                self._new_support_seen = True
                self.use_new = support[0] != 0
                return

            state = package.find_param(_PARAM_STATE)
            if len(state) == 1:
                await self._update_state(state[0] != 0)
            return

        if package.command_id == CMD_BIG_VOLUME_LEGACY_QUERY:
            state = package.find_param(_PARAM_STATE)
            if len(state) == 1:
                await self._update_state(state[0] != 0)
            else:
                await self.driver.put_property("sound", "big_volume_supported", "false")

    async def set_property(self, group: str, prop: str, value: str):
        if prop != "big_volume":
            log.warning(f"Property {group}//{prop} is read-only, ignoring write")
            return False

        if not self.supported:
            log.warning("Device doesn't support noisy-environment volume boost, ignoring write")
            return False

        command = CMD_BIG_VOLUME_WRITE if self.use_new else CMD_BIG_VOLUME_LEGACY_WRITE
        resp = await self.driver.send_package(_build_set_rq(command, value == "true"))
        if resp is None:
            log.warning("No response to noisy-environment volume write")
            return False

        if self.use_new:
            resp = await self.driver.send_package(_build_new_state_rq())
        else:
            resp = await self.driver.send_package(_build_legacy_state_rq())
        if resp is not None:
            await self.on_package(resp)
        return True
