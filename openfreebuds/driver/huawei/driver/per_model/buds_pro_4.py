from openfreebuds.driver.huawei.driver.per_model.buds_pro_3 import OfbDriverHuaweiPro3
from openfreebuds.driver.huawei.handler import (OfbHuaweiActionDoubleTapHandler,
                                                OfbHuaweiActionTripleTapHandler,
                                                OfbHuaweiAdaptiveVolumeHandler,
                                                OfbHuaweiHeadControlHandler,
                                                OfbHuaweiSmartChargeHandler)


class OfbDriverHuaweiPro4(OfbDriverHuaweiPro3):
    """
    HUAWEI FreeBuds Pro 4
    """
    def __init__(self, address):
        super().__init__(address)
        self.handlers.extend([
            OfbHuaweiActionDoubleTapHandler(w_in_call=True, w_read_in_call=True),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiAdaptiveVolumeHandler(),
            OfbHuaweiHeadControlHandler(),
            OfbHuaweiSmartChargeHandler(),
        ])
