from openfreebuds.driver.huawei.driver.per_model.buds_pro_3 import OfbDriverHuaweiPro3
from openfreebuds.driver.huawei.handler import OfbHuaweiHeadControlHandler


class OfbDriverHuaweiFreeClip(OfbDriverHuaweiPro3):
    """
    HUAWEI FreeClip (1st gen)
    """
    def __init__(self, address):
        super().__init__(address)
        # 初代 FreeClip 只在 Pro 3 基础上增加头部控制（只读），
        # 不支持耳机端独立空间音频与充电盒提示音自定义
        self.handlers.append(OfbHuaweiHeadControlHandler())
