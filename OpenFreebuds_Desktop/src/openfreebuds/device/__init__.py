import logging

from openfreebuds.device.base import BaseDevice
from openfreebuds.device.spp_device import SPPDevice

log = logging.getLogger("OpenfreebudsDeviceRoot")
DEVICE_PROFILES = {
    "HUAWEI FreeBuds 4i": SPPDevice,
    "generic": SPPDevice
}


def is_supported(name: str):
    return name in DEVICE_PROFILES


def create(name: str, address: str) -> BaseDevice:
    if name not in DEVICE_PROFILES:
        log.warning("USING GENERIC DEVICE PROFILE")
        name = "generic"

    return DEVICE_PROFILES[name](address)
