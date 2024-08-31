from openfreebuds.driver.huawei.constants import CMD_TRIPLE_TAP_READ, CMD_TRIPLE_TAP_WRITE
from openfreebuds.driver.huawei.handler.abstract.multi_tap import FbHuaweiAbstractTapActionHandler


class FbHuaweiActionTripleTapHandler(FbHuaweiAbstractTapActionHandler):
    """
    Triple tap config handler
    """

    handler_id = "gesture_triple"
    commands = [CMD_TRIPLE_TAP_READ, CMD_TRIPLE_TAP_WRITE]

    properties = [
        ("action", "triple_tap_left"),
        ("action", "triple_tap_right"),
        ("action", "triple_tap_in_call"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prop_prefix = "triple_tap"
        self.cmd_read = CMD_TRIPLE_TAP_READ
        self.cmd_write = CMD_TRIPLE_TAP_WRITE
