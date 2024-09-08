from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuaweiLacePro(OfbDriverHuaweiGeneric):
    def __init__(self, address):
        super().__init__(address)

        # Add cooldown to prevent device hang
        self._spp_connect_delay = 2

        self.handlers = [
            # Drop2b03Handler(),
            OfbHuaweiInfoHandler(),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiAncHandler(w_cancel_lvl=True),
            OfbHuaweiAncLegacyChangeHandler(),
            OfbHuaweiActionsPowerButtonHandler(),
            OfbHuaweiActionLongTapHandler(),
            OfbHuaweiVoiceLanguageHandler(),
        ]
