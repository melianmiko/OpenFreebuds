import asyncio
from contextlib import suppress
from typing import Optional

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.utils import OfbCoreEvent

log = create_logger("OfbQtAutomationService")


class OfbQtAutomationService:
    instance = None

    def __init__(self, ofb: IOpenFreebuds):
        self.ofb = ofb
        self.config = OfbQtConfigParser.get_instance()

        self._task: Optional[asyncio.Task] = None

    @staticmethod
    def get_instance(ofb: IOpenFreebuds):
        if OfbQtAutomationService.instance is None:
            OfbQtAutomationService.instance = OfbQtAutomationService(ofb)
        return OfbQtAutomationService.instance

    async def stop(self):
        if self._task is not None:
            with suppress(Exception):
                self._task.cancel()
                await self._task
            self._task = None

    async def start(self):
        await self.stop()
        # if not self.config.get("automation", "enabled", False):
        #     return

        self._task = asyncio.create_task(self._main())

    async def _handle(self, event: OfbCoreEvent):
        if event.kind_match(OfbEventKind.STATE_CHANGED):
            if event.args[0] == IOpenFreebuds.STATE_DISCONNECTED:
                await self._trigger("on_disconnect")
            elif event.args[0] == IOpenFreebuds.STATE_CONNECTED:
                await self._trigger("on_connect")

    async def _trigger(self, local_kind: str):
        shortcut = self.config.get("automation", local_kind, False)
        if not shortcut:
            return

        log.info(f"Trigger shortcut {shortcut} due to automation event {local_kind}")
        await self.ofb.run_shortcut(shortcut)

    async def _main(self):
        log.info("Started")
        member_id = await self.ofb.subscribe(kind_filters=[OfbEventKind.STATE_CHANGED])

        while True:
            try:
                event = OfbCoreEvent(*await self.ofb.wait_for_event(member_id))
                await self._handle(event)
            except Exception:
                log.exception("Failure")
