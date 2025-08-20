import asyncio
from contextlib import suppress
from typing import Optional

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.utils import OfbCoreEvent

import sys

try:
    from openfreebuds_backend.linux.dbus.mpris import MPRISPProxy
except ImportError:
    MPRISPProxy = None

# Import Windows media control if on Windows
if sys.platform == "win32":
    try:
        from openfreebuds_backend.windows.media_win32 import WindowsMediaControl
    except ImportError:
        WindowsMediaControl = None
else:
    WindowsMediaControl = None

log = create_logger("OfbQtMPRISHelperService")


class OfbQtMPRISHelperService:
    instance = None

    def __init__(self, ofb: IOpenFreebuds):
        self.ofb = ofb
        self.config = OfbQtConfigParser.get_instance()

        self._task: Optional[asyncio.Task] = None
        self.paused_players: list[MPRISPProxy] = []
        self.last_in_ear: Optional[bool] = None  # None = primeira execução

    async def _trigger(self):
        in_ear = await self.ofb.get_property("state", "in_ear", "false") == "true"
        # HARDCODED: Always enable auto-pause regardless of config
        enabled = True  # Force auto-pause to always be enabled

        # DEBUG: Log estado atual
        print(f"[AUTO-PAUSE] in_ear: {in_ear}, last_in_ear: {self.last_in_ear}")
        
        # Skip auto-pause na primeira execução para evitar pause inicial
        if self.last_in_ear is None:
            print("[AUTO-PAUSE] Primeira execução - salvando estado inicial")
            self.last_in_ear = in_ear
            return
        
        if in_ear != self.last_in_ear and enabled:
            print(f"[AUTO-PAUSE] Mudança detectada! {self.last_in_ear} -> {in_ear}")
            if self.last_in_ear is True and in_ear is False:
                # Pause all
                print("[AUTO-PAUSE] REMOVIDO - pausando players")
                self.paused_players = []
                
                # Use appropriate media control based on platform
                if sys.platform == "win32" and WindowsMediaControl:
                    services = await WindowsMediaControl.get_all()
                elif MPRISPProxy:
                    services = await MPRISPProxy.get_all()
                else:
                    log.warning("No media control available for this platform")
                    services = []
                
                for service in services:
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
        # Enable by default on Windows if media control is available
        if sys.platform == "win32":
            should_start = WindowsMediaControl is not None
        else:
            should_start = self.config.get("mpris", "enabled", False)
        
        if not should_start:
            return

        self._task = asyncio.create_task(self._main())

    async def _main(self):
        log.info("Started")
        print("[AUTO-PAUSE] Serviço MPRIS iniciado - escutando eventos in_ear")
        member_id = await self.ofb.subscribe(kind_filters=[OfbEventKind.PROPERTY_CHANGED])

        while True:
            try:
                event = OfbCoreEvent(*await self.ofb.wait_for_event(member_id))
                if event.is_changed("state", "in_ear"):
                    print("[AUTO-PAUSE] Evento in_ear detectado - chamando _trigger()")
                    await self._trigger()
            except Exception:
                log.exception("Failure")
