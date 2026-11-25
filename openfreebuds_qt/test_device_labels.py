from collections import Counter

from openfreebuds_qt.utils.device_labels import format_device_label


def test_duplicate_device_names_append_uppercase_address():
    devices = [
        {"name": "HUAWEI FreeClip 2", "address": "c0:e5:79:45:6c:95"},
        {"name": "HUAWEI FreeClip 2", "address": "11:22:33:44:55:66"},
    ]
    counts = Counter(device["name"] for device in devices)

    assert format_device_label(devices[0]["name"], devices[0]["address"], counts) == \
        "HUAWEI FreeClip 2 [C0:E5:79:45:6C:95]"
    assert format_device_label(devices[1]["name"], devices[1]["address"], counts) == \
        "HUAWEI FreeClip 2 [11:22:33:44:55:66]"


def test_unique_device_name_keeps_plain_label():
    counts = Counter(["HUAWEI FreeClip 2", "HUAWEI FreeBuds 5"])

    assert format_device_label("HUAWEI FreeClip 2", "AA:BB:CC:DD:EE:FF", counts) == \
        "HUAWEI FreeClip 2"
