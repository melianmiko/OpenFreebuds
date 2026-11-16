from openfreebuds.driver.huawei.driver.per_model.buds_pro_3 import OfbDriverHuaweiPro3
from openfreebuds.driver.huawei.handler import OfbHuaweiHeadControlHandler


class OfbDriverHuaweiPro4(OfbDriverHuaweiPro3):
    """
    HUAWEI FreeBuds Pro 4
    """
    def __init__(self, address):
        super().__init__(address)
        # FreeBuds Pro 4 adds head control (read-only) on top of Pro 3
        self.handlers.append(OfbHuaweiHeadControlHandler())
