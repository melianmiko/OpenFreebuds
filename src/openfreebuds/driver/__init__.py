from openfreebuds.driver.huawei.driver.buds_5i import FbDriverHuawei5i

DEVICE_TO_DRIVER_MAP = {
    "HUAWEI FreeBuds 5i": FbDriverHuawei5i,
}


def is_device_supported(name: str):
    return name in DEVICE_TO_DRIVER_MAP
