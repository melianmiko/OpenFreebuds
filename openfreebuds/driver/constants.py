from openfreebuds.driver.huawei import OfbDriverHuawei5I, OfbDriverHuaweiSe, OfbDriverHuaweiLacePro, OfbDriverHuawei4I, \
    OfbDriverHuaweiPro, OfbDriverHuaweiPro2, OfbDriverHuaweiPro3

DEVICE_TO_DRIVER_MAP = {
    "HUAWEI FreeBuds 5i": OfbDriverHuawei5I,
    "HUAWEI FreeBuds SE": OfbDriverHuaweiSe,
    "HUAWEI FreeLace Pro": OfbDriverHuaweiLacePro,
    "HUAWEI FreeBuds 4i": OfbDriverHuawei4I,
    "HUAWEI FreeBuds Pro": OfbDriverHuaweiPro,
    "HUAWEI FreeBuds Pro 2": OfbDriverHuaweiPro2,
    "HUAWEI FreeBuds Pro 3": OfbDriverHuaweiPro3,
}
