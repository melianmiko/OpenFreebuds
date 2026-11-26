import json

from openfreebuds.driver.huawei.constants import (
    CMD_LEFT_RIGHT_AUTO,
    CMD_LEFT_RIGHT_AUTO_WRITE,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiLeftRightAutoHandler")

# Official LeftRightEarRecognitionCard:
#   read  2b 9a 01 00  -> parameter 1, empty
#   write 2b 99 01 01 <0/1> -> parameter 1, one byte switch state
_PARAM_ENABLED = 1


def _build_read_rq():
    """Build the 0x2B9A left/right auto-switch query: 01 00."""
    return HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_AUTO, [
        (_PARAM_ENABLED, b""),
    ])


def _build_write_rq(enabled: bool):
    """Build the 0x2B99 left/right auto-switch write: 01 01 <0/1>."""
    return HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_AUTO_WRITE, [
        (_PARAM_ENABLED, 1 if enabled else 0),
    ])


class OfbHuaweiLeftRightAutoHandler(OfbDriverHandlerHuawei):
    """Left/right auto-switch handler (read 0x2B9A, write 0x2B99).

    Official config declares isLeftRightEarSupport on FreeClip, FreeClip 2
    and FreeClip 2 S. W Buds 1/2 are mounted because the user requested the
    switch; runtime support is decided by the response's switch field, so an
    unsupported firmware only hides this control.
    """

    handler_id = "config_left_right_auto"
    commands = [CMD_LEFT_RIGHT_AUTO, CMD_LEFT_RIGHT_AUTO_WRITE]
    init_timeout = 1
    init_attempt_max = 2
    properties = [
        ("config", "left_right_auto"),
        ("config", "left_right_auto_supported"),
    ]

    def __init__(self):
        self.supported: bool = False

    async def on_init(self):
        resp = await self.driver.send_package(_build_read_rq())
        if resp is None:
            await self.driver.put_property("config", "left_right_auto_supported", "false")
            return

        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None:
            return
        if package.command_id == CMD_LEFT_RIGHT_AUTO_WRITE:
            # The write ACK only reports the command result; the state is
            # delivered by 0x2B9A, or updated optimistically after the ACK.
            return
        if package.command_id != CMD_LEFT_RIGHT_AUTO:
            return

        state = package.find_param(_PARAM_ENABLED)
        if len(state) != 1:
            # Empty echo means this firmware does not expose the switch
            self.supported = False
            await self.driver.put_property("config", "left_right_auto_supported", "false")
            return

        self.supported = True
        await self.driver.put_property("config", None, {
            "left_right_auto_supported": "true",
            "left_right_auto": json.dumps(state[0] != 0),
        }, extend_group=True)

    async def set_property(self, group: str, prop: str, value: str):
        if prop != "left_right_auto":
            log.warning(f"Property {group}//{prop} is read-only, ignoring write")
            return False

        if not self.supported:
            log.warning("Device doesn't support left/right auto-switch, ignoring write")
            return False

        enabled = value == "true"
        resp = await self.driver.send_package(_build_write_rq(enabled))
        if resp is None:
            log.warning("No response for left/right auto-switch write")
            return False

        # 0x2B99 only acknowledges the write. Update the visible state now;
        # a later 0x2B9A notification can still correct it if the firmware
        # rejects the value.
        await self.driver.put_property("config", "left_right_auto", json.dumps(enabled))
        return True
