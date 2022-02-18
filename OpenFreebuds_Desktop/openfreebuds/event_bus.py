import logging
import threading

log = logging.getLogger("EventBus")
root_condition = threading.Condition()
conditions = {}


def invoke(event_name: str):
    # Send root notification
    with root_condition:
        root_condition.notify_all()

    # Send specific notification
    if event_name in conditions:
        with conditions[event_name]:
            conditions[event_name].notify_all()


def wait_any(timeout=None):
    with root_condition:
        root_condition.wait(timeout=timeout)


def wait_for(event_name, timeout=None):
    if event_name not in conditions:
        conditions[event_name] = threading.Condition()

    with conditions[event_name]:
        conditions[event_name].wait(timeout=timeout)
