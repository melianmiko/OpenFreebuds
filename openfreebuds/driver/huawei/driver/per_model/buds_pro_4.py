from openfreebuds.driver.huawei.driver.per_model.buds_pro_3 import OfbDriverHuaweiPro3
from openfreebuds.driver.huawei.handler import OfbHuaweiHeadControlHandler


class OfbDriverHuaweiPro4(OfbDriverHuaweiPro3):
    """
    HUAWEI FreeBuds Pro 4
    """
    def __init__(self, address):
        super().__init__(address)
        # FreeBuds Pro 4 在 Pro 3 基础上增加头部控制（只读）
        self.handlers.append(OfbHuaweiHeadControlHandler())
