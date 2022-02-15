import threading
import time

from openfreebuds.spp.device import SPPDevice


class FreebudsManager:
    MAINLOOP_TIMEOUT = 2

    STATE_NO_DEV = 0
    STATE_OFFLINE = 1
    STATE_DISCONNECTED = 2
    STATE_WAIT = 3
    STATE_CONNECTED = 4

    def __init__(self):
        self.device = None
        self.address = None

        self.started = False
        self.state = self.STATE_NO_DEV

        self.scan_results = []
        self.state_changed = threading.Event()
        self.scan_complete = threading.Event()
        self.on_close = threading.Event()

    def scan(self, lock=False, timeout=None):
        self.scan_complete.clear()
        self.scan_results = []

        threading.Thread(target=self._do_scan).start()

        if lock:
            self.scan_complete.wait(timeout=timeout)

    def set_device(self, address):
        self.address = address

        self.on_close.clear()
        threading.Thread(target=self._mainloop).start()

    def close(self):
        self.started = False
        self.on_close.wait()

    def _close_device(self):
        # Close spp if it was started
        if self.device is None:
            return

        self.device.close()
        self.device = None

    def set_state(self, state):
        if state == self.state:
            return

        self.state = state
        self.state_changed.set()

    def _mainloop(self):
        self.started = True

        # Check that spp exists in paired
        if not self._device_exists():
            self.set_state(self.STATE_NO_DEV)
            self.started = False
            return

        while self.started:
            # If offline, update state and wait
            if not self._is_connected():
                self.set_state(self.STATE_OFFLINE)
                self._close_device()
                time.sleep(self.MAINLOOP_TIMEOUT)
                continue

            # Create dev and connect if not
            if not self.device:
                self.set_state(self.STATE_WAIT)
                self.device = SPPDevice(self.address)
                self.device.connect()

            # If disconnected, wipe all and try again
            if not self.device.started:
                self.set_state(self.STATE_DISCONNECTED)
                self._close_device()
                continue

            # If all is OK, just chill
            self.set_state(self.STATE_CONNECTED)
            self.device.on_close.wait(timeout=self.MAINLOOP_TIMEOUT)

        # Exit main loop
        self._close_device()
        self.on_close.set()

    def _device_exists(self):
        raise Exception("Must be override")

    def _do_scan(self):
        raise Exception("Must be override")

    def _is_connected(self):
        raise Exception("Must be override")
