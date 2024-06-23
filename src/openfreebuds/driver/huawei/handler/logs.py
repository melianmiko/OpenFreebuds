from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei


class FbHuaweiLogsHandler(FbDriverHandlerHuawei):
    """
    Ignore hardware logging
    """
    handler_id = "drop_logs"
    ignore_commands = [b"\x0a\x0d"]
