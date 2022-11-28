import logging
import queue
import threading

log = logging.getLogger("EventBus")


class Data:
    listeners = []
    event_name = ""


class Listener(queue.Queue):
    def __init__(self):
        super().__init__()
        self.filters = []

    def invoke(self, name):
        if name in self.filters:
            self.put_nowait(name)

    def close(self):
        Data.listeners.remove(self)

    def wait(self, timeout=None):
        try:
            return self.get(timeout=timeout)
        except queue.Empty:
            pass


def invoke(event_name: str):
    for listener in Data.listeners:
        listener.invoke(event_name)


def wait_for(ev_filter, timeout=None):
    if isinstance(ev_filter, str):
        ev_filter = [ev_filter]

    listener = register(ev_filter)
    listener.wait(timeout=timeout)
    listener.close()


def register(ev_filter):
    listener = Listener()
    listener.filters = ev_filter
    Data.listeners.append(listener)

    return listener
