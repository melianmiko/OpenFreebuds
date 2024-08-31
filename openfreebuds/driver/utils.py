from openfreebuds.driver import DEVICE_TO_DRIVER_MAP


def is_device_supported(name: str):
    return name in DEVICE_TO_DRIVER_MAP
