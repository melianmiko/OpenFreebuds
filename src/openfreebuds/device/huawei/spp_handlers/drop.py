import logging

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler

log = logging.getLogger("HuaweiHandlers")


class DropLogsHandler(HuaweiSppHandler):
    handler_id = "drop_logs"
    ignore_commands = [b"\x0a\x0d"]
