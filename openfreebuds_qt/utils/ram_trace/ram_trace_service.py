import asyncio
import os
import signal
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Optional

import psutil
from pympler.tracker import SummaryTracker

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.generic import IOfbQtApplication
from openfreebuds_qt.utils import OfbQtReportTool

log = create_logger("OfbQtRamTraceService")
ram_warn = 256 * 1024 * 1024                # 256bb
ram_exit = 512 * 1024 * 1024                # 512gb


class OfbQtRamTraceService:
    def __init__(self, ctx: IOfbQtApplication):
        self._task: Optional[asyncio.Task] = None
        self.tracker = SummaryTracker()
        self.last_print = datetime.now() - timedelta(days=1)
        self.ctx = ctx

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._mainloop())

    def _write_trace(self):
        data = [""]
        for item in self.tracker.format_diff():
            data.append(item)
        log.warn("\n".join(data))

    async def _mainloop(self):
        process = psutil.Process()
        await asyncio.sleep(15)
        log.info("Start up RAM usage trace")
        self._write_trace()

        with suppress(asyncio.CancelledError):
            log.info("Started")
            while True:
                current_usage = process.memory_info().rss
                if current_usage > ram_exit:
                    log.error("RAM usage exceeded")
                    self._write_trace()
                    async with asyncio.Timeout(5):
                        await OfbQtReportTool(self.ctx).create_and_show()
                    log.error("Force exiting...")

                    # noinspection PyProtectedMember,PyUnresolvedReferences
                    os._exit(1)
                    os.kill(os.getpid(), signal.SIGKILL)
                elif current_usage > ram_warn and datetime.now() > self.last_print + timedelta(minutes=5):
                    log.warn(f"Too high ram usage, print trace info")
                    self._write_trace()
                    self.last_print = datetime.now()
                await asyncio.sleep(10)
