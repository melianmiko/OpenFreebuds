import asyncio
from typing import Optional

from openfreebuds import IOpenFreebuds
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config import OfbQtConfigParser

log = create_logger("OfbQtHotkeyService")


class OfbQtHotkeyService:
    instance = None

    def __init__(self, ofb: IOpenFreebuds):
        self.ofb = ofb
        self.config = OfbQtConfigParser.get_instance()
        self.pynput: Optional[any] = None

    @staticmethod
    def get_instance(ofb: IOpenFreebuds):
        if OfbQtHotkeyService.instance is None:
            OfbQtHotkeyService.instance = OfbQtHotkeyService(ofb)
        return OfbQtHotkeyService.instance

    def start(self):
        self.stop()
        if not self.config.get("hotkeys", "enabled", False):
            return

        try:
            from pynput.keyboard import GlobalHotKeys
            self.pynput = GlobalHotKeys(self._create_handlers())
            self.pynput.start()
            log.debug("Started hotkey tool.")
        except ValueError:
            log.warn("Can't start GlobalHotKeys")
        except ImportError as e:
            log.warn(f"Can't start GlobalHotkeys due to {e}")

    def _create_handlers(self):
        out: dict[str, callable] = {}
        for shortcut, hotkey in self.config.get("hotkeys").items():
            if shortcut == "enabled":
                continue
            log.debug(f"Set up {hotkey} => {shortcut}")
            out[hotkey] = self._get_action(shortcut, asyncio.get_event_loop())
        return out

    def _get_action(self, shortcut, loop):
        def _inner():
            fut = asyncio.run_coroutine_threadsafe(self.ofb.run_shortcut(shortcut), loop)
            fut.result()
        return _inner

    def stop(self):
        if self.pynput is not None:
            self.pynput.stop()
            self.pynput = None
