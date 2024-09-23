import asyncio
from contextlib import suppress
from typing import Optional

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.utils import OfbCoreEvent

try:
    from openfreebuds_backend.linux.dbus.mpris import MPRISPProxy
except ImportError:
    MPRISPProxy = None

log = create_logger("OfbQtMPRISHelperService")


class OfbQtMPRISHelperService:
    instance = None

    def __init__(self, ofb: IOpenFreebuds):
        self.ofb = ofb
        self.config = OfbQtConfigParser.get_instance()

        self._task: Optional[asyncio.Task] = None
        self.paused_players: list[MPRISPProxy] = []
        self.last_in_ear: bool = True

    async def _trigger(self):
        in_ear = await self.ofb.get_property("state", "in_ear", "false") == "true"
        enabled = await self.ofb.get_property("config", "auto_pause", "false") == "true"

        if in_ear != self.last_in_ear and enabled:
            if self.last_in_ear is True and in_ear is False:
                # Pause all
                self.paused_players = []
                for service in await MPRISPProxy.get_all():
                    if await service.playback_status() == "Playing":
                        log.info(f"Pause {await service.identity()}")
                        await service.pause()
                        self.paused_players.append(service)
            elif self.last_in_ear is False and in_ear is True:
                for service in self.paused_players:
                    log.info(f"Resume {await service.identity()}")
                    await service.play()
                self.paused_players = []
            self.last_in_ear = in_ear

    @staticmethod
    def get_instance(ofb: IOpenFreebuds):
        if OfbQtMPRISHelperService.instance is None:
            OfbQtMPRISHelperService.instance = OfbQtMPRISHelperService(ofb)
        return OfbQtMPRISHelperService.instance

    async def stop(self):
        if self._task is not None:
            with suppress(Exception):
                self._task.cancel()
                await self._task
            self._task = None

    async def start(self):
        await self.stop()
        if not self.config.get("mpris", "enabled", False):
            return

        self._task = asyncio.create_task(self._main())

    async def _main(self):
        log.info("Started")
        member_id = await self.ofb.subscribe(kind_filters=[OfbEventKind.PROPERTY_CHANGED])

        while True:
            try:
                event = OfbCoreEvent(*await self.ofb.wait_for_event(member_id))
                if event.is_changed("state", "in_ear"):
                    await self._trigger()
            except Exception:
                log.exception("Failure")
