from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.device.generic.virtual_device import VirtualDevice
from openfreebuds.device.huawei.profiles import (FreeLaceProDevice, FreeBuds4iDevice, FreeBudsSEDevice,
                                                 FreeBudsPro3Device, FreeBuds5iDevice)

PROFILES = {
    "HUAWEI FreeBuds SE": FreeBudsSEDevice,
    "HUAWEI FreeLace Pro": FreeLaceProDevice,
    "HUAWEI FreeBuds 4i": FreeBuds4iDevice,
    "HUAWEI FreeBuds 5i": FreeBuds5iDevice,
    "HUAWEI FreeBuds Pro 3": FreeBudsPro3Device,
    "Debug: Virtual device": VirtualDevice
}

# (implementation_level, profile)
SUPPORTED_DEVICES = {
    "HUAWEI FreeBuds SE": ("full", FreeBudsSEDevice),

    "HUAWEI FreeLace Pro": ("full", FreeLaceProDevice),

    "HUAWEI FreeBuds 4i": ("full", FreeBuds4iDevice),
    "HONOR Earbuds 2 Lite": ("full", FreeBuds4iDevice),
    "HUAWEI FreeBuds Pro 2": ("partial", FreeBuds4iDevice),

    "HUAWEI FreeBuds 5i": ("partial", FreeBuds5iDevice),

    "HUAWEI FreeBuds Pro 3": ("partial", FreeBudsPro3Device),

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
