from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.device.huawei.profiles import FreeBuds4iDevice, FreeLaceProDevice

DEVICE_PROFILES = {
    "HUAWEI FreeBuds 4i": FreeBuds4iDevice,
    "HONOR Earbuds 2 Lite": FreeBuds4iDevice,
    "HUAWEI FreeLace Pro": FreeLaceProDevice,
}


def is_supported(name: str):
    return name in DEVICE_PROFILES


def create(name: str, address: str) -> BaseDevice | None:
    if name not in DEVICE_PROFILES:
        return None

    return DEVICE_PROFILES[name](address)
