from openfreebuds.driver.huawei.constants import CMD_DUAL_TAP_READ, CMD_DUAL_TAP_WRITE
from openfreebuds.driver.huawei.handler.abstract.multi_tap import OfbHuaweiAbstractTapActionHandler


class OfbHuaweiActionDoubleTapHandler(OfbHuaweiAbstractTapActionHandler):
    """
    Double tap config handler
    """

    handler_id = "gesture_double"
    commands = [CMD_DUAL_TAP_READ, CMD_DUAL_TAP_WRITE]

    properties = [
        ("action", "double_tap_left"),
        ("action", "double_tap_right"),
        ("action", "double_tap_in_call"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prop_prefix = "double_tap"
        self.cmd_read = CMD_DUAL_TAP_READ
        self.cmd_write = CMD_DUAL_TAP_WRITE
