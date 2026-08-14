from openfreebuds.driver.huawei.constants import CMD_DEVICE_TIME, CMD_HEADSET_SOUND_STATE, CMD_LOG_REPORT_RESULT
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei


class OfbHuaweiLogsHandler(OfbDriverHandlerHuawei):
    """
    Ignore hardware logging
    """
    handler_id = "drop_logs"
    ignore_commands = [b"\x0a\x0d", CMD_LOG_REPORT_RESULT, CMD_DEVICE_TIME, CMD_HEADSET_SOUND_STATE]
