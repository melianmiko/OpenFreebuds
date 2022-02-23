import logging
import threading
import time

import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.events import EVENT_MANAGER_STATE_CHANGED, EVENT_MANAGER_CLOSE, EVENT_SPP_CLOSED
from openfreebuds.spp.device import SPPDevice


log = logging.getLogger("FreebudsManager")


def create():
    return FreebudsManager()


class FreebudsManager:

    MAINLOOP_TIMEOUT = 4

    STATE_NO_DEV = 0
    STATE_OFFLINE = 1
    STATE_DISCONNECTED = 2
    STATE_WAIT = 3
    STATE_CONNECTED = 4
    STATE_FAILED = 5

    def __init__(self):
        self.device = None
        self.address = None

        self.started = False
        self.state = self.STATE_NO_DEV

        self.scan_results = []

    def set_device(self, address):
        if self.address is not None:
            self.unset_device()

        self.address = address
        threading.Thread(target=self._mainloop).start()

    def unset_device(self, lock=True):
        if not self.started:
            return

        self.address = None
        self.started = False

        self.set_state(self.STATE_NO_DEV)

        if lock:
            event_bus.wait_for(EVENT_MANAGER_CLOSE)

    def close(self, lock=True):
        if not self.started:
            return

        log.info("closing...")
        self.started = False

        if lock:
            event_bus.wait_for(EVENT_MANAGER_CLOSE)

    def _close_device(self):
        # Close spp if it was started
        if self.device is None:
            return

        self.device.close(lock=True)
        self.device = None

    def set_state(self, state):
        if state == self.state:
            return

        self.state = state
        log.info("State changed to " + str(state))
        event_bus.invoke(EVENT_MANAGER_STATE_CHANGED)

    def _mainloop(self):
        self.started = True

        log.debug("Started")

        event_queue = event_bus.register([
            EVENT_SPP_CLOSED
        ])

        # Check that spp exists in paired
        if not openfreebuds_backend.bt_device_exists(self.address):
            log.warning("Device dont exist, bye...")
            self.set_state(self.STATE_NO_DEV)
            self.started = False

        while self.started:
            # If offline, update state and wait
            if not openfreebuds_backend.bt_is_connected(self.address):
                self.set_state(self.STATE_OFFLINE)
                self._close_device()
                time.sleep(self.MAINLOOP_TIMEOUT)
                continue

            # Create dev and connect if not
            if not self.device:
                log.info("Trying to create SPP device and connect...")
                self.set_state(self.STATE_WAIT)
                self.device = SPPDevice(self.address)
                status = self.device.connect()

                if not status:
                    log.warning("Can't create SPP connection, exit...")
                    self.set_state(self.STATE_FAILED)
                    time.sleep(self.MAINLOOP_TIMEOUT)
                    continue

            # If disconnected, wipe all and try again
            if self.device.closed:
                log.warning("SPP connection closed")
                self.set_state(self.STATE_DISCONNECTED)
                self._close_device()
                continue

            # If all is OK, just chill
            self.set_state(self.STATE_CONNECTED)
            event_queue.wait(timeout=self.MAINLOOP_TIMEOUT)

        # Exit main loop
        log.info("leaving manager thread...")
        self._close_device()

        event_queue.close()
        event_bus.invoke(EVENT_MANAGER_CLOSE)
