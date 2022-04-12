import logging
import os
import threading
import webbrowser

from openfreebuds_applet.modules import actions

log = logging.getLogger("HotkeysTool")


class _PynputState:
    current = None


def test_available():
    try:
        from pynput import keyboard
        return True, ""
    except ImportError as e:
        return False, str(e)


def test_os_supported():
    if "XDG_SESSION_TYPE" in os.environ:
        if os.environ["XDG_SESSION_TYPE"] == "wayland":
            return False, "wayland"

    return True, ""


def start(applet):
    if _PynputState.current is not None:
        _PynputState.current.stop()

    if not applet.settings.enable_hotkeys:
        return

    if not test_available()[0]:
        log.error("Can't start hotkeys tool: service don't available")
        return

    log.debug("Starting hotkey tool...")

    from pynput.keyboard import GlobalHotKeys
    handlers = actions.get_actions(applet)
    config = applet.settings.hotkeys_config_2
    merged = {}

    for a in handlers:
        if a in config and config[a] != "":
            merged[config[a]] = handlers[a]

    _PynputState.current = GlobalHotKeys(merged)
    _PynputState.current.start()
    log.debug("Started hotkey tool.")


class HotkeyRecorder:
    ignored_keys = ["<65511>", "<65032>"]

    def __init__(self):
        self.working = False
        self._specials = []
        self._result = False
        self._main_key = ""
        self.ready_ev = threading.Event()
        self.listener = None

    def record(self, sync=False):
        from pynput import keyboard

        self.ready_ev.clear()
        self.working = True
        self._result = False
        self._main_key = ""
        self._specials = []

        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

        if sync:
            self.ready_ev.wait()

    def _finish(self):
        self.listener.stop()
        self.ready_ev.set()
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

    def on_press(self, key):
        from pynput import keyboard
        if isinstance(key, keyboard.Key):
            val = str(key).replace("Key.", "")
            if val not in self._specials:
                self._specials.append(val)

    def on_release(self, key):
        from pynput import keyboard
        if isinstance(key, keyboard.Key):
            val = str(key).replace("Key.", "")
            if val == "esc":
                self.cancel()
                return
            if val in self._specials:
                self._specials.remove(val)
        elif str(key) not in self.ignored_keys:
            self._main_key = str(key)
            self._result = True
            self._finish()


def _wayland_callback(result):
    if result:
        webbrowser.open("https://melianmiko.ru/posts/openfreebuds-faq/")
