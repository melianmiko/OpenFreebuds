from openfreebuds.driver.huawei.driver.per_model.buds_pro_3 import OfbDriverHuaweiPro3
from openfreebuds.driver.huawei.handler import OfbHuaweiDropReminderHandler, OfbHuaweiHeadControlHandler


class OfbDriverHuaweiFreeClip(OfbDriverHuaweiPro3):
    """
    HUAWEI FreeClip (1st gen)
    """
    def __init__(self, address):
        super().__init__(address)
        # First-gen FreeClip only adds head control (read-only) on top of Pro 3;
        # it does not support standalone spatial audio on the earbuds or custom charging-case tones
        self.handlers.append(OfbHuaweiHeadControlHandler())
        self.handlers.append(OfbHuaweiDropReminderHandler())
