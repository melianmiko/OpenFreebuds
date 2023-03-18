from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.device import huawei


DEVICE_PROFILES = huawei.devices


def is_supported(name: str):
    return name in DEVICE_PROFILES


def create(name: str, address: str) -> BaseDevice | None:
    if name not in DEVICE_PROFILES:
        return None

    return DEVICE_PROFILES[name](address)
