import asyncio
import ctypes
import os
import subprocess
import webbrowser

# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.bluetooth import BluetoothDevice
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.networking import HostName

from openfreebuds.utils.logger import create_logger
from openfreebuds_applet.l18n import t
from openfreebuds_backend.errors import BluetoothNotAvailableError

extra_tools_dir = 'C:\\Program Files (x86)\\Bluetooth Command Line Tools\\bin'
extra_tools_url = "https://bluetoothinstaller.com/bluetooth-command-line-tools/BluetoothCLTools-1.2.0.56.exe"
log = create_logger("WindowsBackend")

no_console = subprocess.STARTUPINFO()
no_console.dwFlags |= subprocess.STARTF_USESHOWWINDOW


def bt_is_connected(address):
    async def run():
        try:
            host_name = HostName(address)
            bt_device = await BluetoothDevice.from_host_name_async(host_name)
            return bt_device.connection_status
        except OSError:
            log.info("Got OSError, looks like Bluetooth isn't available")
            return False

    return asyncio.run(run())


def bt_connect(address):
    if not _tools_ready():
        return False

    base_args = [extra_tools_dir + "\\btcom.exe", "-b\"{}\"".format(address)]

    try:
        _run_commands([
            base_args + ["-r", "-s111e"],
            base_args + ["-r", "-s110b"]
        ])
        _run_commands([
            base_args + ["-c", "-s111e"],
            base_args + ["-c", "-s110b"]
        ])
        return True
    except subprocess.CalledProcessError:
        log.exception("Can't connect device")
        return False


def bt_disconnect(address):
    if not _tools_ready():
        return False

    base_args = [extra_tools_dir + "\\btcom.exe", "-b\"{}\"".format(address)]

    try:
        _run_commands([
            base_args + ["-r", "-s111e"],
            base_args + ["-r", "-s110b"]
        ])
        return True
    except subprocess.CalledProcessError:
        log.exception("Can't disconnect device")
        return False


def bt_device_exists(address):
    devices = bt_list_devices()

    for a in devices:
        if a["address"] == address:
            return True

    return False


def bt_list_devices():
    out = []

    async def run():
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

    return asyncio.run(run())


def _run_commands(commands):
    processes = []
    for cmd in commands:
        r = subprocess.Popen(cmd, startupinfo=no_console)
        processes.append(r)
    for a in processes:
        a.wait()


def _tools_ready():
    if os.path.isdir(extra_tools_dir):
        return True

    response = ctypes.windll.user32.MessageBoxW(
        None,
        t("To use this feature, you must install \"Bluetooth Command Line Tools\"\n "
          "from bluetoothinstaller.com. Without this, you can't use connect/disconnect\n"
          "features on Windows. Notice that this software is provided \"as is\" and don't\n"
          "give any warranty of any kind.\n\n"
          "For more information, visit https://bluetoothinstaller.com\n\n"
          "Also note, that this tools may not work on newer versions of MS Windows, like ver. 11.\n"
          "Open browser to download installer?"),
        "Openfreebuds",
        4)
    if response == 6:
        webbrowser.open(extra_tools_url)

    return response
