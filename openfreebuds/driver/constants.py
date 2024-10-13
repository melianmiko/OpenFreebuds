from openfreebuds.driver.generic_debug import *
from openfreebuds.driver.huawei import *

DEVICE_TO_DRIVER_MAP = {
    "HUAWEI FreeBuds 5i": OfbDriverHuawei5I,
    "HUAWEI FreeBuds 6i": OfbDriverHuawei6I,
    "HUAWEI FreeBuds SE": OfbDriverHuaweiSe,
    "HUAWEI FreeLace Pro": OfbDriverHuaweiLacePro,
    "HUAWEI FreeLace Pro 2": OfbDriverHuaweiLacePro2,
    "HUAWEI FreeBuds 4i": OfbDriverHuawei4I,
    "HONOR Earbuds 2": OfbDriverHuawei4I,
    "HUAWEI FreeBuds Pro": OfbDriverHuaweiPro,
    "HUAWEI FreeBuds Pro 2": OfbDriverHuaweiPro2,
    "HUAWEI FreeBuds Pro 3": OfbDriverHuaweiPro3,
    "Debug: Virtual device": OfbFileDeviceDriver,
}
