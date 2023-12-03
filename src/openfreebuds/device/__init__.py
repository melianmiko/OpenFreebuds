from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.device.generic.virtual_device import VirtualDevice
from openfreebuds.device.huawei.profiles import FreeLaceProDevice, FreeBuds4iDevice, FreeBudsSEDevice

PROFILES = {
    "HUAWEI FreeBuds 4i": FreeBuds4iDevice,
    "HUAWEI FreeLace Pro": FreeLaceProDevice,
    "HUAWEI FreeBuds SE": FreeBudsSEDevice,
    "Debug: Virtual device": VirtualDevice
}

# (implementation_level, profile)
SUPPORTED_DEVICES = {
    "HUAWEI FreeBuds 4i": ("full", FreeBuds4iDevice),
    "HONOR Earbuds 2 Lite": ("full", FreeBuds4iDevice),
    "HUAWEI FreeLace Pro": ("full", FreeLaceProDevice),
    "HUAWEI FreeBuds SE": ("full", FreeBudsSEDevice),

    "HUAWEI FreeBuds 5i": ("partial", FreeBuds4iDevice),
    "HUAWEI FreeBuds Pro 2": ("partial", FreeBuds4iDevice),

    "Debug: Virtual device": ("virtual", VirtualDevice),
}


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
