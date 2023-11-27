from openfreebuds.device.huawei.profiles import FreeLaceProDevice, FreeBuds4iDevice, FreeBudsSEDevice

profiles = {
    "HUAWEI FreeBuds 4i": FreeBuds4iDevice,
    "HUAWEI FreeLace Pro": FreeLaceProDevice,
    "HUAWEI FreeBuds SE" : FreeBudsSEDevice
}

# (implementation_level, profile)
devices = {
    "HUAWEI FreeBuds 4i": ("full", FreeBuds4iDevice),
    "HONOR Earbuds 2 Lite": ("full", FreeBuds4iDevice),
    "HUAWEI FreeLace Pro": ("full", FreeLaceProDevice),
    "HUAWEI FreeBuds SE": ("full", FreeBudsSEDevice),

    "HUAWEI FreeBuds 5i": ("partial", FreeBuds4iDevice),
    "HUAWEI FreeBuds Pro 2": ("partial", FreeBuds4iDevice),
}
