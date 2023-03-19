from openfreebuds.device.huawei.profiles import FreeLaceProDevice, FreeBuds4iDevice

profiles = {
    "HUAWEI FreeBuds 4i": FreeBuds4iDevice,
    "HUAWEI FreeLace Pro": FreeLaceProDevice,
}

# (implementation_level, profile)
devices = {
    "HUAWEI FreeBuds 4i": ("full", FreeBuds4iDevice),
    "HONOR Earbuds 2 Lite": ("full", FreeBuds4iDevice),
    "HUAWEI FreeLace Pro": ("full", FreeLaceProDevice),

    "HUAWEI FreeBuds 5i": ("partial", FreeBuds4iDevice),
    "HUAWEI FreeBuds Pro 2": ("partial", FreeBuds4iDevice),
}
