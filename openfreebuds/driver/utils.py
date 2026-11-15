from openfreebuds.driver import DEVICE_TO_DRIVER_MAP


def is_device_supported(name: str):
    return name in DEVICE_TO_DRIVER_MAP


def get_display_device_names():
    """
    Device names for user-facing lists: skip bluetooth-name aliases
    (e.g. internal codenames) that exist only for auto-detection.
    """
    return [
        name for name in DEVICE_TO_DRIVER_MAP
        if name.startswith(("HUAWEI ", "HONOR ", "Debug:"))
    ]
