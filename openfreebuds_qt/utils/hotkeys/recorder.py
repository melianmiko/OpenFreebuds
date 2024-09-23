import asyncio
import sys

from openfreebuds.utils.logger import create_logger

log = create_logger("OfbQtHotkeyRecorder")


class OfbQtHotkeyRecorder:
    ignored_keys = ["<65511>", "<65032>"]

    def __init__(self):
        self.working = False
        self._specials = []
        self._result = False
        self._main_key = ""
        self.listener = None

    async def record(self):
        from pynput import keyboard

        if self.working:
            return False

        self.working = True
        self._result = False
        self._main_key = ""
        self._specials = []

        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        log.debug("Recording...")

        while self.working:
            await asyncio.sleep(0.5)

        return self.get_value()

    def _finish(self):
        self.listener.stop()
        self.working = False

    def cancel(self):
        self._result = False
        self._finish()

    def get_value(self):
        if not self._result or len(self._specials) < 1:
            return None

        result = ""
        for a in self._specials:
            result += "<{}>+".format(a)
        result += str(self._main_key).replace("'", "")
        return result

    def on_press(self, pressed_key):
        from pynput import keyboard
        if isinstance(pressed_key, keyboard.Key):
            val = str(pressed_key)\
                .replace("Key.", "")\
                .replace("_l", "")
            if val not in self._specials:
                self._specials.append(val)
                log.debug(f"Add special {val}")

    def on_release(self, pressed_key):
        from pynput import keyboard
        if isinstance(pressed_key, keyboard.Key):
            val = str(pressed_key).replace("Key.", "")
            if val == "esc" and len(self._specials) == 1:
                self.cancel()
                return
            if val in self._specials:
                self._specials.remove(val)
        elif str(pressed_key) not in self.ignored_keys:
            if len(self._specials) < 1:
                return
            if sys.platform == "win32":
                pressed_key = _parse_win32_key_vk(pressed_key.vk)
            self._main_key = str(pressed_key)
            self._result = True
            log.debug("Ready")
            self._finish()


def _parse_win32_key_vk(vk: int):
    return vk.to_bytes(length=1, byteorder="big", signed=False).decode("utf8")
