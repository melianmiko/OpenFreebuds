import asyncio
import logging
import os
import subprocess

# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.bluetooth import BluetoothDevice
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.networking import HostName

from openfreebuds_backend.errors import BluetoothNotAvailableError
from openfreebuds_backend.exception import OfbBackendDependencyMissingError

extra_tools_dir = 'C:\\Program Files (x86)\\Bluetooth Command Line Tools\\bin'
extra_tools_url = "https://bluetoothinstaller.com/bluetooth-command-line-tools/BluetoothCLTools-1.2.0.56.exe"
log = logging.getLogger("OfbWindowsBackend")

no_console = subprocess.STARTUPINFO()
no_console.dwFlags |= subprocess.STARTF_USESHOWWINDOW


async def bt_is_connected(address):
    try:
        host_name = HostName(address)
        bt_device = await BluetoothDevice.from_host_name_async(host_name)
        return bt_device.connection_status
    except OSError:
        log.info("Got OSError, looks like Bluetooth isn't available")
        return False


async def bt_connect(address):
    if not os.path.isdir(extra_tools_dir):
        raise OfbBackendDependencyMissingError("Bluetooth Command Line Tools required", extra_tools_url)

    base_args = [extra_tools_dir + "\\btcom.exe", "-b\"{}\"".format(address)]

    try:
        await _run_commands([
            base_args + ["-r", "-s111e"],
            base_args + ["-r", "-s110b"]
        ])
        await _run_commands([
            base_args + ["-c", "-s111e"],
            base_args + ["-c", "-s110b"]
        ])
        return True
    except subprocess.CalledProcessError:
        log.exception("Can't connect device")
        return False


async def bt_disconnect(address):
    if not os.path.isdir(extra_tools_dir):
        raise OfbBackendDependencyMissingError("Bluetooth Command Line Tools required", extra_tools_url)

    base_args = [extra_tools_dir + "\\btcom.exe", "-b\"{}\"".format(address)]

    try:
        await _run_commands([
            base_args + ["-r", "-s111e"],
            base_args + ["-r", "-s110b"]
        ])
        await asyncio.sleep(1)
        return True
    except subprocess.CalledProcessError:
        log.exception("Can't disconnect device")
        return False


async def bt_list_devices():
    out = []
    try:
        selector = BluetoothDevice.get_device_selector_from_pairing_state(True)
        devices = await DeviceInformation.find_all_async(selector, [], DeviceInformationKind.DEVICE)
    except OSError:
        raise BluetoothNotAvailableError("Got OSError, looks like bluetooth isn't installed")

    for a in devices:
        try:
            bt_device = await BluetoothDevice.from_id_async(a.id)
            out.append({
                "name": bt_device.name,
                "address": bt_device.host_name.raw_name[1:-1],
                "connected": bt_device.connection_status
            })
        except OSError:
            pass

    return out


async def _run_commands(commands):
    await asyncio.gather(
        *[asyncio.create_subprocess_exec(*cmd, startupinfo=no_console) for cmd in commands]
    )
