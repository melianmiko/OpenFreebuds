from openfreebuds.driver.huawei.driver.per_model.buds_pro_3 import OfbDriverHuaweiPro3
from openfreebuds.driver.huawei.handler import (OfbHuaweiActionDoubleTapHandler,
                                                OfbHuaweiActionTripleTapHandler,
                                                OfbHuaweiDropReminderHandler,
                                                OfbHuaweiHeadControlHandler)


class OfbDriverHuaweiFreeClip(OfbDriverHuaweiPro3):
    """
    HUAWEI FreeClip (1st gen)
    """
    def __init__(self, address):
        super().__init__(address)
        # First-gen FreeClip only has double/triple tap. It does not support
        # light-hold, long-press, swipe, or standalone spatial audio on the
        # earbuds. It has other charging-case tones, but no writable lid-open
        # tone page, so it keeps the master-only box tone handler from Pro 3.
        unsupported = {
            "gesture_light_hold",
            "gesture_long_split",
            "gesture_swipe",
            "config_spatial_audio",
        }
        self.handlers = [h for h in self.handlers if h.handler_id not in unsupported]
        self.handlers.extend([
            OfbHuaweiActionDoubleTapHandler(w_in_call=True, w_read_in_call=True),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiHeadControlHandler(),
            OfbHuaweiDropReminderHandler(),
        ])
