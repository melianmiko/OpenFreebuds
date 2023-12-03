import logging

from openfreebuds.device.huawei.generic.spp_handler import HuaweiSppHandler
from openfreebuds.logger import create_log

log = create_log("HuaweiHandlers")


class DropLogsHandler(HuaweiSppHandler):
    handler_id = "drop_logs"
    ignore_commands = [b"\x0a\x0d"]
