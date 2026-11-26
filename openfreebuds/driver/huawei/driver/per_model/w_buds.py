from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import (
    OfbHuaweiBatteryHandler,
    OfbHuaweiInfoHandler,
    OfbHuaweiLeftRightAutoHandler,
)


class OfbDriverHuaweiWBuds(OfbDriverHuaweiGeneric):
    """HUAWEI W Buds / W Buds 2.

    Model ids 000137 (Saga, productId ZAAA) and 00016F (Libra, productId
    ZAAX). No official settings profile exists in the 2.0.7.321 assets, so
    this driver keeps only identity, battery and the left/right auto-switch.
    The switch is mounted because the user requested it; the handler hides
    itself when the firmware does not answer 0x2B9A.
    """

    supports_find_earbud = False

    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiLeftRightAutoHandler(),
        ]
