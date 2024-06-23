from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class FbDriverHuaweiSe(FbDriverHuaweiGeneric):
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            FbHuaweiLogsHandler(),
            FbHuaweiInfoHandler(),
            FbHuaweiBatteryHandler(),
            FbHuaweiActionDoubleTapHandler(),
        ]
