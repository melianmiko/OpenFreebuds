from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class FbDriverHuaweiLacePro(FbDriverHuaweiGeneric):
    def __init__(self, address):
        super().__init__(address)

        # Add cooldown to prevent device hang
        self._spp_connect_delay = 2

        self.handlers = [
            # Drop2b03Handler(),
            FbHuaweiInfoHandler(),
            FbHuaweiBatteryHandler(),
            FbHuaweiAncHandler(w_cancel_lvl=True),
            FbHuaweiAncLegacyChangeHandler(),
            FbHuaweiActionsPowerButtonHandler(),
            FbHuaweiActionLongTapHandler(),
        ]
