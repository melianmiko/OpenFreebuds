import re

from openfreebuds import is_device_supported

# Official Huawei Smart Audio 2.0.7.321 filter data:
# assets/config/device_whitelist.json, version 35.
# The Android app checks the Bluetooth device name with these patterns, which
# lets it list paired Huawei devices even when they are currently disconnected.
_HUAWEI_AUDIO_NAME_PREFIXES = (
    "HUAWEI FreeBuds",
    "HUAWEI FreeClip",
    "HUAWEI FreeLace",
    "HUAWEI FreeArc",
    "HUAWEI Eyewear",
    "HUAWEI W Buds",
    "HUAWEI WATCH Buds",
    "HONOR Earbuds",
    "HONOR Magic Earbuds",
)

_HUAWEI_BT_NAME_PATTERN_TEXTS = (
    r"^(?=(FreeBuds 3|Shark))",
    r"^(?=(HUAWEI FreeBuds 3i))",
    r"^(?=(HUAWEI FreeLace Pro|Nile))",
    r"^(?=(ROC|HUAWEI FreeBuds X|HUAWEI FreeBuds Studio))",
    r"^(?=(MermaidTWS|M 1|M1))|HUAWEI FreeBuds Pro$",
    r"^(?=(HUAWEI FreeBuds 4i))",
    r"^(?=(Hero|HUAWEI FreeBuds 4))",
    r"^(?=(HUAWEI FreeBuds Lipstick))",
    r"^(?=(puffer|Puffer|HUAWEI FreeBuds SE))",
    r"^(?=(RHEIN|Rhein|HUAWEI FreeLace 活力版))",
    r"^(?=(HUAWEI FreeBuds 4E))",
    r"^(?=(Nemo 尊享版$|nemo 尊享版$))",
    r"^(?=(HUAWEI FreeBuds Pro 2$))",
    r"^(?=(HUAWEI FreeBuds 5i))",
    r"^(?=(Honey|HONEY)|HUAWEI FreeBuds 5$)",
    r"^(?=(HUAWEI FreeBuds SE 2|ULC))",
    r"^(?=(PIANO|M3))|HUAWEI FreeBuds Pro 3$",
    r"^(?=(HUAWEI FreeLace Pro 2))",
    r"^(?=(Diva|HUAWEI FreeBuds Lipstick 2))",
    r"^(?=(Harper-T00$|Harper$))|HUAWEI FreeBuds 6$",
    r"^(?=(PianoH$|pianoH$))|HUAWEI FreeBuds Pro 4$",
    r"^(?=(HUAWEI FreeBuds SE 3))",
    r"^(?=(Harper-T01$|Harper$))|HUAWEI FreeBuds 6$",
    r"^(?=(HUAWEI FreeBuds SE 5 MAX))",
    r"^(?=(HUAWEI FreeBuds Pro 5))",
    r"^(?=(HUAWEI Eyewear))",
    r"^(?=(HUAWEI Eyewear 2))",
    r"^(?=(HUAWEI FreeBuds 7$))",
    r"^(?=(HUAWEI FreeBuds Neo))",
    r"^(?=(HUAWEI FreeClip 2 典藏版|HUAWEI FreeClip 2 S))",
)

_HUAWEI_BT_NAME_PATTERNS = tuple(re.compile(pattern) for pattern in _HUAWEI_BT_NAME_PATTERN_TEXTS)


def is_huawei_audio_device(name: str) -> bool:
    """Match the official Huawei Bluetooth name whitelist."""
    if not name:
        return False

    if name.startswith(_HUAWEI_AUDIO_NAME_PREFIXES):
        return True

    return any(pattern.search(name) for pattern in _HUAWEI_BT_NAME_PATTERNS)


def is_default_visible_device(name: str) -> bool:
    """Devices shown before enabling the unsupported-device checkbox."""
    return is_huawei_audio_device(name) or is_device_supported(name)


def filter_paired_devices(
    devices: list[dict],
    show_unsupported: bool = False,
    current_address: str | None = None,
) -> list[dict]:
    """Keep the current device and known Huawei-family devices. When unsupported
    devices are enabled, restore the original list of all paired devices."""
    if show_unsupported:
        return list(devices)

    current = (current_address or "").lower()
    results = []

    for device in devices:
        name = device.get("name") or ""
        address = device.get("address") or ""

        keep = is_default_visible_device(name)
        if current and address.lower() == current:
            keep = True

        if keep:
            results.append(device)

    return results
