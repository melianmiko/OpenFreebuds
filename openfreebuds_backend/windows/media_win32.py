"""Windows media sessions (SMTC) proxy, same interface as the Linux MPRIS proxy."""
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)


class MPRISPProxy:
    def __init__(self, session):
        self.session = session

    @staticmethod
    async def get_all():
        manager = await SessionManager.request_async()
        return [MPRISPProxy(s) for s in manager.get_sessions()]

    async def pause(self):
        return await self.session.try_pause_async()

    async def play(self):
        return await self.session.try_play_async()

    async def identity(self) -> str:
        return self.session.source_app_user_model_id

    async def playback_status(self) -> str:
        info = self.session.get_playback_info()
        if info is not None and info.playback_status == PlaybackStatus.PLAYING:
            return "Playing"
        return "Paused"
