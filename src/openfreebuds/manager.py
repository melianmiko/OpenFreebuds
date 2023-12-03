import logging
import threading
import time
from typing import Optional

import openfreebuds.device
import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.device.generic.base import DeviceConfig, BaseDevice
from openfreebuds.constants.events import EVENT_MANAGER_STATE_CHANGED, EVENT_MANAGER_CLOSE, EVENT_SPP_CLOSED
from openfreebuds.logger import create_log

log = create_log("FreebudsManager")


class FreebudsManager:
    _manager = None

    MAINLOOP_TIMEOUT = 1

    STATE_NO_DEV = 0
    STATE_OFFLINE = 1
    STATE_DISCONNECTED = 2
    STATE_WAIT = 3
    STATE_CONNECTED = 4
    STATE_FAILED = 5
    STATE_PAUSED = 6

    @staticmethod
    def get():
        if FreebudsManager._manager is None:
            FreebudsManager._manager = FreebudsManager(True)
        return FreebudsManager._manager

    def __init__(self, singleton_lock=False):
        self.device_name = None
        self.device_address = None
        self.device: Optional[BaseDevice] = None

        self._paused = False
        self._must_leave = False
        self._thread = None                 # type: threading.Thread|None
        self.state = self.STATE_NO_DEV
        self.config = DeviceConfig()

        if not singleton_lock:
            raise ValueError("Use FreebudsManager.get()")

    def set_device(self, name, address):
        if self.device_name == name and self.device_address == address:
            log.info("Device already attached, ignoring set_device")
            return

        self.device_name = name
        self.device_address = address

        log.debug("Waiting for finish current manager...")
        self.close(True)

        self._must_leave = False
        if self.config.SAFE_RUN_WRAPPER is None:
            self._thread = threading.Thread(target=self._mainloop)
            self._thread.start()
        else:
            log.debug("Running mainloop via safe wrapper")
            self._thread = self.config.SAFE_RUN_WRAPPER(self._mainloop, "ManagerThread", False)

    def _is_thread_alive(self):
        return self._thread is not None and self._thread.is_alive()

    def close(self, lock=True):
        """
        Exit manager thread NOW
        """
        if not self._is_thread_alive():
            log.info("Don't started, nothing to close")
            return

        log.info("Closing manager thread...")
        self._must_leave = True

        if lock:
            self._thread.join()

        log.info("Manager thread closed from close()...")

    def _close_device(self):
        # Close spp if it was started
        if self.device is None:
            return

        self.device.close(lock=True)
        self.device = None

    def set_paused(self, val):
        self._paused = val

        if val:
            self.set_state(self.STATE_PAUSED)

    def set_state(self, state):
        if state == self.state:
            return

        self.state = state
        log.info("State changed to " + str(state))
        event_bus.invoke(EVENT_MANAGER_STATE_CHANGED)

    def _device_disconnected(self):
        return (not openfreebuds_backend.bt_is_connected(self.device_address)
                and not self.device_address == "00:00:00:00:00:00")

    def _mainloop(self):
        log.debug("Started")

        event_queue = event_bus.register([
            EVENT_SPP_CLOSED
        ])

        if self.device_address is None or self.device_name is None:
            log.warning("No device")
            self._must_leave = True

        while not self._must_leave:
            if self._paused:
                log.debug("Manager thread paused")
                time.sleep(self.MAINLOOP_TIMEOUT)
                self.set_state(self.STATE_PAUSED)
                continue

            # If offline, update state and wait
            if self._device_disconnected():
                self.set_state(self.STATE_OFFLINE)
                self._close_device()
                time.sleep(self.MAINLOOP_TIMEOUT)
                continue

            # Create dev and connect if not
            if not self.device:
                log.info("Trying to create device and connect...")
                self.set_state(self.STATE_WAIT)
                self.device = openfreebuds.device.create(self.device_name, self.device_address)
                if not self.device:
                    self.set_state(self.STATE_FAILED)
                    continue
                self.device.config = self.config
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
        log.info("Thread finished")
