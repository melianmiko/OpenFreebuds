import json

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_DROP_REMINDER
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiDropReminderHandler")

# 0x2BB4 payload fields (measured 2026-11-16 on FreeClip 2):
#   1 = featureId (echoes 0x07)
#   2 = switch (0 = off, 1 = on)
_PARAM_FEATURE = 1
_PARAM_ENABLED = 2


def _build_read_rq():
    """Build the 0x2BB4 drop-reminder query: 01 01 07"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_DROP_REMINDER),
    ])


def _build_write_rq(enabled: bool):
    """Build the 0x2BB4 drop-reminder switch write: 01 01 07 02 01 <0/1>"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_DROP_REMINDER),
        (_PARAM_ENABLED, 1 if enabled else 0),
    ])


class OfbHuaweiDropReminderHandler(OfbDriverHandlerHuawei):
    """Drop-reminder handler (0x2BB4 MBB, featureId 7).
    The official config declares drop_detection on FreeClip / FreeBuds 6 / FreeClip 2 / FreeClip 2 S / FreeBuds 7. If the device does not respond, only supported=false is set, and the UI hides the whole group without affecting other features. FreeBuds Neo declares the flag but is not exposed because it is not in the supported model list.
    """

    handler_id = "config_drop_reminder"
    commands = [CMD_MBB_FEATURE]
    init_timeout = 1
    init_attempt_max = 2
    properties = [
        ("config", "drop_reminder"),
        ("config", "drop_reminder_supported"),
    ]

    def __init__(self):
        self.supported: bool = False

    async def on_init(self):
        resp = await self.driver.send_package(_build_read_rq())
        if resp is None:
            await self.driver.put_property("config", "drop_reminder_supported", "false")
            return

        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None or package.command_id != CMD_MBB_FEATURE:
            return

        feature = package.find_param(_PARAM_FEATURE)
        if len(feature) == 0 or feature[0] != MBB_FEATURE_DROP_REMINDER:
            return

        state = package.find_param(_PARAM_ENABLED)
        if len(state) != 1:
            # Feature echo only, no switch field -> this firmware does not support it
            self.supported = False
            await self.driver.put_property("config", "drop_reminder_supported", "false")
            return

        self.supported = True
        await self.driver.put_property("config", None, {
            "drop_reminder_supported": "true",
            "drop_reminder": json.dumps(state[0] != 0),
        }, extend_group=True)

    async def set_property(self, group: str, prop: str, value: str):
        if prop != "drop_reminder":
            log.warning(f"Property {group}//{prop} is read-only, ignoring write")
            return False

        if not self.supported:
            log.warning("Device doesn't support drop reminder, ignoring write")
            return False

        resp = await self.driver.send_package(_build_write_rq(value == "true"))
        if resp is not None:
            await self.on_package(resp)
        return True
