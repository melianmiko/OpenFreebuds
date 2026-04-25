import asyncio
import logging
from contextlib import suppress

import IOBluetooth

log = logging.getLogger("OfbDarwinBackend")


def _canonical_address(addr: str) -> str:
    """Normalize a Bluetooth MAC to colon-separated upper-case form."""
    return addr.replace("-", ":").upper()


def _find_device(address: str):
    addr = _canonical_address(address)
    # IOBluetoothDevice.deviceWithAddressString_ accepts both dash and colon forms
    return IOBluetoothDevice_deviceWithAddressString(addr) or \
        IOBluetoothDevice_deviceWithAddressString(addr.replace(":", "-").lower())


def IOBluetoothDevice_deviceWithAddressString(addr: str):
    return IOBluetooth.IOBluetoothDevice.deviceWithAddressString_(addr)


async def bt_is_connected(address):
    with suppress(Exception):
        device = _find_device(address)
        if device is None:
            return None
        return bool(device.isConnected())
    return False


async def bt_connect(address):
    try:
        device = _find_device(address)
        if device is None:
            return None
        err = await asyncio.to_thread(device.openConnection)
        await asyncio.sleep(1)
        return err == 0
    except Exception:
        log.exception(f"Failed to connect {address}")
        return False


async def bt_disconnect(address):
    try:
        device = _find_device(address)
        if device is None:
            return None
        err = await asyncio.to_thread(device.closeConnection)
        await asyncio.sleep(1)
        return err == 0
    except Exception:
        log.exception(f"Failed to disconnect {address}")
        return False


async def bt_list_devices():
    results = []
    with suppress(Exception):
        devices = await asyncio.to_thread(IOBluetooth.IOBluetoothDevice.pairedDevices)
        if not devices:
            return results
        for dev in devices:
            try:
                name = dev.name() or dev.nameOrAddress() or "(unnamed)"
                raw_addr = dev.addressString() or ""
                addr = _canonical_address(raw_addr)
                connected = bool(dev.isConnected())
                if not addr:
                    continue
                results.append({
                    "name": str(name),
                    "address": addr,
                    "connected": connected,
                })
            except Exception:
                log.debug("Skip broken IOBluetooth device", exc_info=True)
    return results
