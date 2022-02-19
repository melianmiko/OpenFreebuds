import logging
import threading

log = logging.getLogger("EventBus")


class Data:
    cv = threading.Condition()
    event_name = ""


def invoke(event_name: str):
    # Send root notification
    with Data.cv:
        Data.event_name = event_name
        Data.cv.notify_all()


def wait_any(timeout=None):
    with Data.cv:
        Data.cv.wait(timeout)
        return Data.event_name


def wait_for(event_name, timeout=None):
    with Data.cv:
        Data.cv.wait(timeout)
        if Data.event_name == event_name:
            return Data.event_name
