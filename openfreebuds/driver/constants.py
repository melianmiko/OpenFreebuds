from openfreebuds.driver.generic_debug import *
from openfreebuds.driver.huawei import *

DEVICE_TO_DRIVER_MAP = {
    "HONOR Earbuds 2": OfbDriverHuawei4I,
    "HONOR Earbuds 2 SE": OfbDriverHuawei4I,
    "HONOR Earbuds 2 Lite": OfbDriverHuawei4I,
    "HUAWEI FreeBuds 4i": OfbDriverHuawei4I,
    "HUAWEI FreeBuds 5i": OfbDriverHuawei5I,
    "HUAWEI FreeBuds 6i": OfbDriverHuawei6I,
    "HUAWEI FreeBuds Pro": OfbDriverHuaweiPro,
    "HUAWEI FreeBuds Pro 2": OfbDriverHuaweiPro2,
    "HUAWEI FreeBuds Pro 3": OfbDriverHuaweiPro3,
    "HUAWEI FreeBuds SE": OfbDriverHuaweiSe,
    "HUAWEI FreeBuds SE 2": OfbDriverHuaweiSe2,
    "HUAWEI FreeBuds Studio": OfbDriverHuaweiStudio,
    "HUAWEI FreeLace Pro": OfbDriverHuaweiLacePro,
    "HUAWEI FreeLace Pro 2": OfbDriverHuaweiLacePro2,
    "Debug: Virtual device": OfbFileDeviceDriver,
}
