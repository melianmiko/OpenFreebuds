from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.device.generic.virtual_device import VirtualDevice
from openfreebuds.device.huawei.profiles.buds_4i import FreeBuds4iDevice
from openfreebuds.device.huawei.profiles.buds_5i import FreeBuds5iDevice
from openfreebuds.device.huawei.profiles.buds_pro import FreeBudsProDevice
from openfreebuds.device.huawei.profiles.buds_pro_2 import FreeBudsPro2Device
from openfreebuds.device.huawei.profiles.buds_pro_3 import FreeBudsPro3Device
from openfreebuds.device.huawei.profiles.buds_se import FreeBudsSEDevice
from openfreebuds.device.huawei.profiles.lace_pro import FreeLaceProDevice

PROFILES = {
    "HUAWEI FreeBuds SE": FreeBudsSEDevice,
    "HUAWEI FreeLace Pro": FreeLaceProDevice,
    "HUAWEI FreeBuds 4i": FreeBuds4iDevice,
    "HUAWEI FreeBuds 5i": FreeBuds5iDevice,
    "HUAWEI FreeBuds Pro": FreeBudsProDevice,
    "HUAWEI FreeBuds Pro 2": FreeBudsPro2Device,
    "HUAWEI FreeBuds Pro 3": FreeBudsPro3Device,
}

# (implementation_level, profile)
SUPPORTED_DEVICES = {
    "HUAWEI FreeLace Pro": ("full", FreeLaceProDevice),
    "HUAWEI FreeBuds SE": ("full", FreeBudsSEDevice),
    "HUAWEI FreeBuds 4i": ("full", FreeBuds4iDevice),
    "HUAWEI FreeBuds 5i": ("full", FreeBuds5iDevice),
    "HUAWEI FreeBuds Pro": ("partial", FreeBudsProDevice),
    "HUAWEI FreeBuds Pro 2": ("partial", FreeBudsPro2Device),
    "HUAWEI FreeBuds Pro 3": ("partial", FreeBudsPro3Device),

    "HONOR Earbuds 2 Lite": ("full", FreeBuds4iDevice),
}


def is_supported(name: str):
    if name not in SUPPORTED_DEVICES:
        return False

    level, profile = SUPPORTED_DEVICES[name]
    return level == "full" or level == "partial"


def create(name: str, address: str) -> BaseDevice | None:
    if address == "00:00:00:00:00:00":
        return VirtualDevice(address)
    if name not in SUPPORTED_DEVICES:
        return None

    level, profile = SUPPORTED_DEVICES[name]
    return profile(address)
