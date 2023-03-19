from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.device import huawei


SUPPORTED_DEVICES = huawei.devices
PROFILES = huawei.profiles


def is_supported(name: str):
    if name not in SUPPORTED_DEVICES:
        return False

    level, profile = SUPPORTED_DEVICES[name]
    return level == "full" or level == "partial"


def create(name: str, address: str) -> BaseDevice | None:
    if name not in SUPPORTED_DEVICES:
        return None

    level, profile = SUPPORTED_DEVICES[name]
    return profile(address)
