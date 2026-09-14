from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


FREEBUDS_3_DOUBLE_TAP_OPTIONS = {
    -1: "tap_action_off",
    0: "tap_action_assistant",
    1: "tap_action_pause",
    3: "tap_action_switch_anc",
    4: "tap_action_next",
}


class OfbDriverHuawei3(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds 3
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiLogsHandler(),
            OfbHuaweiInfoHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiActionDoubleTapHandler(options_map=FREEBUDS_3_DOUBLE_TAP_OPTIONS),
            OfbHuaweiVoiceLanguageHandler(),
        ]
