from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class FbDriverHuawei4i(FbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds 4i
    """
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            FbHuaweiLogsHandler(),
            FbHuaweiInfoHandler(),
            FbHuaweiStateInEarHandler(),
            FbHuaweiAncHandler(),
            FbHuaweiBatteryHandler(),
            FbHuaweiActionDoubleTapHandler(),
            FbHuaweiActionLongTapSplitHandler(),
            FbHuaweiConfigAutoPauseHandler(),
            FbHuaweiVoiceLanguageHandler(),
        ]
