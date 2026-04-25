"""SDP attribute walkers for IOBluetoothSDPServiceRecord, used to resolve RFCOMM
channel IDs without relying on PyObjC's broken bridging metadata for
`getRFCOMMChannelID:` and friends. Validated against a real FreeBuds Pro 4."""
from __future__ import annotations

import logging

log = logging.getLogger("OfbDarwinSDP")

# SDP type codes (Bluetooth Core spec, Vol3 Part B)
_SDP_TYPE_UINT = 1
_SDP_TYPE_UUID = 3
_SDP_TYPE_SEQ = 6
_SDP_TYPE_ALT = 7

# Well-known SDP UUIDs (16-bit short form)
_UUID_RFCOMM = 0x0003
_UUID_SPP = 0x1101

# SDP attribute IDs
_ATTR_SERVICE_CLASS_ID_LIST = 0x0001
_ATTR_PROTOCOL_DESCRIPTOR_LIST = 0x0004

_BT_BASE_UUID_TAIL = bytes.fromhex("00001000800000805F9B34FB")


def _attrs_as_dict(svc) -> dict:
    raw = svc.attributes()
    if raw is None:
        return {}
    out = {}
    for k in raw:
        try:
            out[int(k)] = raw[k]
        except Exception:
            pass
    return out


def _seq(elem) -> list:
    try:
        td = elem.getTypeDescriptor()
        if td not in (_SDP_TYPE_SEQ, _SDP_TYPE_ALT):
            return []
        arr = elem.getArrayValue()
        return list(arr) if arr is not None else []
    except Exception:
        return []


def _uint(elem):
    try:
        if elem.getTypeDescriptor() != _SDP_TYPE_UINT:
            return None
        n = elem.getNumberValue()
        return int(n) if n is not None else None
    except Exception:
        return None


def _uuid16(elem):
    try:
        if elem.getTypeDescriptor() != _SDP_TYPE_UUID:
            return None
        u = elem.getUUIDValue()
        if u is None:
            return None
        # IOBluetoothSDPUUID inherits from NSData. Normalize to 16-bit when possible.
        try:
            u16 = u.getUUIDWithLength_(2)
            data = bytes(u16) if u16 is not None else None
            if data and len(data) == 2:
                return int.from_bytes(data, "big")
        except Exception:
            pass
        try:
            length = int(u.length())
            data = bytes(u)[:length] if length else b""
        except Exception:
            data = b""
        if len(data) == 2:
            return int.from_bytes(data, "big")
        if len(data) == 4:
            v = int.from_bytes(data, "big")
            return (v & 0xFFFF) if (v >> 16) == 0 else v
        if len(data) == 16 and data[4:] == _BT_BASE_UUID_TAIL:
            return int.from_bytes(data[0:4], "big") & 0xFFFF
        return None
    except Exception:
        return None


def _service_rfcomm_channel(svc):
    attrs = _attrs_as_dict(svc)
    pdl = attrs.get(_ATTR_PROTOCOL_DESCRIPTOR_LIST)
    if pdl is None:
        return None
    for protocol_entry in _seq(pdl):
        items = _seq(protocol_entry)
        if not items:
            continue
        if _uuid16(items[0]) == _UUID_RFCOMM and len(items) >= 2:
            return _uint(items[1])
    return None


def _service_class_uuids(svc):
    attrs = _attrs_as_dict(svc)
    out = []
    scl = attrs.get(_ATTR_SERVICE_CLASS_ID_LIST)
    if scl is None:
        return out
    for entry in _seq(scl):
        u = _uuid16(entry)
        if u is not None:
            out.append(u)
    return out


def find_spp_channel(device, fallback: int | None = None) -> int | None:
    """Return the best-guess RFCOMM channel for SPP on `device`.

    Priority:
    1. Service whose ServiceClassIDList includes SPP (0x1101).
    2. Service whose RFCOMM channel matches `fallback` (the per-model port).
    3. Service whose name is exactly "Serial Port".
    4. None — caller falls back to `fallback`.
    """
    candidates: list[tuple[int, str | None, list[int]]] = []
    services = device.services() or []
    for svc in services:
        ch = _service_rfcomm_channel(svc)
        if ch is None:
            continue
        name = svc.getServiceName() if hasattr(svc, "getServiceName") else None
        uuids = _service_class_uuids(svc)
        candidates.append((ch, name, uuids))

    if not candidates:
        log.debug("No RFCOMM-capable services found on device")
        return None

    log.debug(f"RFCOMM candidates: {candidates}")

    for ch, name, uuids in candidates:
        if _UUID_SPP in uuids:
            return ch
    if fallback is not None:
        for ch, _name, _uuids in candidates:
            if ch == fallback:
                return ch
    for ch, name, _uuids in candidates:
        if name and "serial" in name.lower():
            return ch
    return None
