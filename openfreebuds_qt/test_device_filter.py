import pytest

from openfreebuds_qt.utils.device_filter import (
    filter_paired_devices,
    is_default_visible_device,
    is_huawei_audio_device,
)


@pytest.mark.parametrize("name", [
    "HUAWEI FreeBuds Pro",
    "HUAWEI FreeBuds 5",
    "HUAWEI FreeBuds 6i",
    "HUAWEI FreeBuds 7i",
    "HUAWEI FreeClip 2",
    "HUAWEI FreeClip 2 典藏版",
    "HUAWEI FreeLace Pro 2",
    "HUAWEI FreeArc",
    "HUAWEI Eyewear 2",
    "HUAWEI WATCH Buds 2",
    "Shark",
    "Honey",
    "Nile",
    "Diva",
])
def test_huawei_audio_names_are_recognized(name):
    assert is_huawei_audio_device(name) is True


@pytest.mark.parametrize("name", [
    "Keyboard K380",
    "Poulo 17 Ama Min",
    "AirPods Pro",
    "WH-1000XM5",
    "",
])
def test_non_huawei_names_are_rejected(name):
    assert is_huawei_audio_device(name) is False


def test_supported_honor_family_is_visible_by_default():
    assert is_default_visible_device("HONOR Earbuds 2") is True
    assert is_default_visible_device("HONOR Earbuds 2 SE") is True


def _devices():
    return [
        {"name": "HUAWEI FreeClip 2", "address": "C0:E5:79:45:6C:95"},
        {"name": "HUAWEI FreeBuds Pro", "address": "A4:C7:4B:2C:A3:07"},
        {"name": "HONOR Earbuds 2", "address": "11:22:33:44:55:66"},
        {"name": "AirPods Pro", "address": "22:33:44:55:66:77"},
        {"name": "Keyboard K380", "address": "34:88:5D:9D:F1:57"},
        {"name": "Poulo 17 Ama Min", "address": "74:14:D0:5C:FE:7E"},
        {"name": "Unknown Speaker", "address": "77:66:55:44:33:22"},
    ]


def test_default_filter_keeps_huawei_family_only():
    rows = filter_paired_devices(_devices())

    assert [row["name"] for row in rows] == [
        "HUAWEI FreeClip 2",
        "HUAWEI FreeBuds Pro",
        "HONOR Earbuds 2",
    ]


def test_unsupported_toggle_restores_all_paired_devices():
    rows = filter_paired_devices(_devices(), show_unsupported=True)

    assert [row["name"] for row in rows] == [
        "HUAWEI FreeClip 2",
        "HUAWEI FreeBuds Pro",
        "HONOR Earbuds 2",
        "AirPods Pro",
        "Keyboard K380",
        "Poulo 17 Ama Min",
        "Unknown Speaker",
    ]


def test_current_non_huawei_device_stays_visible():
    rows = filter_paired_devices(_devices(), current_address="34:88:5d:9d:f1:57")

    assert "Keyboard K380" in [row["name"] for row in rows]
    assert "AirPods Pro" not in [row["name"] for row in rows]
