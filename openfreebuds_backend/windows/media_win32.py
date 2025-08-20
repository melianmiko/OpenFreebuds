import ctypes
import ctypes.wintypes
from typing import List, Optional
import asyncio
from openfreebuds.utils.logger import create_logger

log = create_logger("MediaWin32")

# Windows API constants
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_STOP = 0xB2
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

# Windows API functions
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def send_media_key(vk_code: int):
    """Send a media key press to the system"""
    try:
        # Press key
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        # Release key
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        return True
    except Exception as e:
        log.error(f"Failed to send media key {vk_code}: {e}")
        return False

class WindowsMediaProxy:
    """Windows media control proxy that mimics MPRIS interface"""
    
    def __init__(self, name: str = "Windows Media"):
        self.name = name
        self._was_playing = False
    
    async def identity(self) -> str:
        return self.name
    
    async def playback_status(self) -> str:
        # We can't easily detect playback status on Windows without more complex APIs
        # For now, assume it's playing if we haven't paused it
        return "Playing" if not self._was_playing else "Paused"
    
    async def pause(self):
        """Pause media playback"""
        log.info(f"Sending pause command to {self.name}")
        if send_media_key(VK_MEDIA_PLAY_PAUSE):
            self._was_playing = True
    
    async def play(self):
        """Resume media playback"""
        log.info(f"Sending play command to {self.name}")
        if send_media_key(VK_MEDIA_PLAY_PAUSE):
            self._was_playing = False
    
    async def stop(self):
        """Stop media playback"""
        log.info(f"Sending stop command to {self.name}")
        send_media_key(VK_MEDIA_STOP)
        self._was_playing = False
    
    @staticmethod
    async def get_all() -> List['WindowsMediaProxy']:
        """Get all available media players (simplified for Windows)"""
        # On Windows, we'll just return a single proxy that controls system media
        return [WindowsMediaProxy("System Media Player")]

# Export the main class - use basic implementation
WindowsMediaControl = WindowsMediaProxy
