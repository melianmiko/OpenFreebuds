from typing import Mapping


def format_device_label(name: str, address: str, name_counts: Mapping[str, int]) -> str:
    """Append the Bluetooth address when several paired devices share a name."""
    if address and name_counts.get(name, 0) > 1:
        return f"{name} [{address}]"
    return name
