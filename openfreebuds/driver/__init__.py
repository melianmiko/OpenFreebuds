from openfreebuds.driver.huawei.driver import *

DEVICE_TO_DRIVER_MAP = {
    "HUAWEI FreeBuds 5i": FbDriverHuawei5i,
    "HUAWEI FreeBuds SE": FbDriverHuaweiSe,
    "HUAWEI FreeLace Pro": FbDriverHuaweiLacePro,
    "HUAWEI FreeBuds 4i": FbDriverHuawei4i,
    "HUAWEI FreeBuds Pro": FbDriverHuaweiPro,
    "HUAWEI FreeBuds Pro 2": FbDriverHuaweiPro2,
    "HUAWEI FreeBuds Pro 3": FbDriverHuaweiPro3,
}


def is_device_supported(name: str):
    return name in DEVICE_TO_DRIVER_MAP
