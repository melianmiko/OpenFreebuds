import logging

from openfreebuds.device.base import BaseDevice
from openfreebuds.device.profile_freebuds_4i import FreeBuds4iDevice
from openfreebuds.device.huawei_spp_device import HuaweiSPPDevice

log = logging.getLogger("OpenFreebudsDeviceRoot")
DEVICE_PROFILES = {
    "HUAWEI FreeBuds 4i": FreeBuds4iDevice,
    "HONOR Earbuds 2 Lite": FreeBuds4iDevice,
    "generic": HuaweiSPPDevice
}


def is_supported(name: str):
    return name in DEVICE_PROFILES


def create(name: str, address: str) -> BaseDevice:
    if name not in DEVICE_PROFILES:
        log.warning("USING GENERIC DEVICE PROFILE")
        name = "generic"

    return DEVICE_PROFILES[name](address)
