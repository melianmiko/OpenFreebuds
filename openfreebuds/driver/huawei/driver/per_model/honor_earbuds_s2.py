from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHonorEarbudsS2(OfbDriverHuaweiGeneric):
    """
    HONOR Earbuds S2 (SCT-T10)

    Uses the HUAWEI private SPP protocol exposed on the standard serial
    port profile (channel 1), instead of the default channel 16. Gesture
    and auto-pause commands are not answered by this model, so those
    handlers are omitted to avoid slow startup.
    """
    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiLogsHandler(),
            OfbHuaweiInfoHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiAncHandler(w_cancel_lvl=True),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiVoiceLanguageHandler(),
        ]
