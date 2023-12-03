import logging

from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_DEVICE_PROP_CHANGED
from openfreebuds.logger import create_log

log = create_log("BaseDevice")


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
    def __init__(self, _):
        self.config = DeviceConfig()
        self.closed = False
        self.enable_prop_changed_event = True
        self._prop_storage = {}

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

    def set_property(self, group: str, prop: str, value):
        self.on_set_property(group, prop, value)
        if self.enable_prop_changed_event:
            event_bus.invoke(EVENT_DEVICE_PROP_CHANGED)

    def on_set_property(self, group: str, prop: str, value):
        raise Exception("Not overriden")

    def _rewrite_properties(self, all_props):
        self._prop_storage = all_props

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

    def close(self, lock=False):
        raise Exception("Overwrite me!")

    def connect(self):
        raise Exception("Overwrite me!")
