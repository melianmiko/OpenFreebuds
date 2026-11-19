import json

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_SMART_CHARGE
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiSmartChargeHandler")

# 0x2BB4 payload fields (FeatureMbbState$g0, feature key 4):
#   1 = featureId (echoes 0x04)
#   2 = switch (0 = off, 1 = on)
_PARAM_FEATURE = 1
_PARAM_ENABLED = 2


def _build_read_rq():
    """Build the 0x2BB4 smart-charge query: 01 01 04."""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_SMART_CHARGE),
    ])


def _build_write_rq(enabled: bool):
    """Build the 0x2BB4 smart-charge switch write: 01 01 04 02 01 <0/1>."""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, MBB_FEATURE_SMART_CHARGE),
        (_PARAM_ENABLED, 1 if enabled else 0),
    ])


class OfbHuaweiSmartChargeHandler(OfbDriverHandlerHuawei):
    """Smart-charging handler (0x2BB4 MBB, featureId 4).

    The official App declares smart_charge on FreeBuds 6 / 7 / 7i / Neo,
    FreeBuds Pro 4 / Pro 5, FreeClip 2 / 2 S and FreeArc. FreeArc has no
    OpenFreebuds driver yet; the other models mount this handler. Runtime
    support is decided by the switch field in the device response.
    """

    handler_id = "config_smart_charge"
    commands = [CMD_MBB_FEATURE]
    init_timeout = 1
    init_attempt_max = 2
    properties = [
        ("config", "smart_charge"),
        ("config", "smart_charge_supported"),
    ]

    def __init__(self):
        self.supported: bool = False

    async def on_init(self):
        resp = await self.driver.send_package(_build_read_rq())
        if resp is None:
            await self.driver.put_property("config", "smart_charge_supported", "false")
            return

        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None or package.command_id != CMD_MBB_FEATURE:
            return

        feature = package.find_param(_PARAM_FEATURE)
        if len(feature) == 0 or feature[0] != MBB_FEATURE_SMART_CHARGE:
            return

        state = package.find_param(_PARAM_ENABLED)
        if len(state) != 1:
            # Feature echo only, no switch field -> this firmware does not support it
            self.supported = False
            await self.driver.put_property("config", "smart_charge_supported", "false")
            return

        self.supported = True
        await self.driver.put_property("config", None, {
            "smart_charge_supported": "true",
            "smart_charge": json.dumps(state[0] != 0),
        }, extend_group=True)

    async def set_property(self, group: str, prop: str, value: str):
        if prop != "smart_charge":
            log.warning(f"Property {group}//{prop} is read-only, ignoring write")
            return False

        if not self.supported:
            log.warning("Device doesn't support smart charging, ignoring write")
            return False

        resp = await self.driver.send_package(_build_write_rq(value == "true"))
        if resp is not None:
            await self.on_package(resp)
        return True
