from openfreebuds.device.base import BaseDevice
from openfreebuds.device.profile_freebuds_4i import FreeBuds4iDevice
from openfreebuds.device.huawei_spp_device import HuaweiSPPDevice

DEVICE_PROFILES = {
    "HUAWEI FreeBuds 4i": FreeBuds4iDevice,
    "HONOR Earbuds 2 Lite": FreeBuds4iDevice
}


def is_supported(name: str):
    return name in DEVICE_PROFILES


def create(name: str, address: str) -> BaseDevice:
    if name not in DEVICE_PROFILES:
        raise ValueError(f"No profile for {name}")

    return DEVICE_PROFILES[name](address)
