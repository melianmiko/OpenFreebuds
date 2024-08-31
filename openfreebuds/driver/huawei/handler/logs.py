from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei


class OfbHuaweiLogsHandler(OfbDriverHandlerHuawei):
    """
    Ignore hardware logging
    """
    handler_id = "drop_logs"
    ignore_commands = [b"\x0a\x0d"]
