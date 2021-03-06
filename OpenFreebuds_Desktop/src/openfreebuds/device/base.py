import logging

from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_DEVICE_PROP_CHANGED

log = logging.getLogger("BaseDevice")


class DeviceConfig:
    USE_SOCKET_SLEEP = False
    SAFE_RUN_WRAPPER = None


def with_no_prop_changed_event(func):
    def internal(*args, **kwargs):
        args[0].enable_prop_changed_event = False

        func(*args, **kwargs)

        args[0].enable_prop_changed_event = True
        event_bus.invoke(EVENT_DEVICE_PROP_CHANGED)
    return internal


class BaseDevice:
    def __init__(self):
        self.config = DeviceConfig()
        self.closed = False
        self.enable_prop_changed_event = True
        self._prop_storage = {}
        self.recv_handlers = {}
        self.set_property_handlers = {}

    def bind_on_package(self, headers, func):
        for a in headers:
            self.recv_handlers[a] = func

    def bind_set_property(self, group, prop, func):
        self.set_property_handlers[group + "___" + prop] = func

    def find_group(self, group):
        if group not in self._prop_storage:
            return {}

        return self._prop_storage[group]

    def find_property(self, group, prop, fallback=None):
        if group not in self._prop_storage:
            return fallback

        if prop not in self._prop_storage[group]:
            return fallback

        return self._prop_storage[group][prop]

    def set_property(self, group, prop, value):
        if group + "___" + prop not in self.set_property_handlers:
            raise Exception("This property isn't writable")
        self.set_property_handlers[group + "___" + prop](value)

    def put_group(self, group, value):
        self._prop_storage[group] = value
        if self.enable_prop_changed_event:
            event_bus.invoke(EVENT_DEVICE_PROP_CHANGED)

    def put_property(self, group, prop, value):
        if group not in self._prop_storage:
            self._prop_storage[group] = {}

        self._prop_storage[group][prop] = value
        if self.enable_prop_changed_event:
            event_bus.invoke(EVENT_DEVICE_PROP_CHANGED)

    def list_properties(self):
        return self._prop_storage

    def send_command(self, ints, read=False):
        raise Exception("Overwrite me!")

    def close(self, lock=False):
        raise Exception("Overwrite me!")

    def connect(self):
        raise Exception("Overwrite me!")
