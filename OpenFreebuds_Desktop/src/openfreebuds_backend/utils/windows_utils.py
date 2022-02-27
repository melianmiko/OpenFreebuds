import ctypes
import logging
import os
import webbrowser

# noinspection PyUnresolvedReferences
from winsdk.windows.devices.bluetooth import BluetoothDevice
# noinspection PyUnresolvedReferences
from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
# noinspection PyUnresolvedReferences
from winsdk.windows.networking import HostName
# noinspection PyUnresolvedReferences
from winsdk.windows.ui.viewmanagement import UISettings, UIColorType

from openfreebuds_applet.l18n import t

extra_tools_dir = 'C:\\Program Files (x86)\\Bluetooth Command Line Tools\\bin'
extra_tools_url = "https://bluetoothinstaller.com/bluetooth-command-line-tools/BluetoothCLTools-1.2.0.56.exe"


async def win_list_bt_devices():
    out = []

    try:
        selector = BluetoothDevice.get_device_selector_from_pairing_state(True)
        devices = await DeviceInformation.find_all_async(selector, [], DeviceInformationKind.DEVICE)
        for a in devices:
            bt_device = await BluetoothDevice.from_id_async(a.id)
            out.append({
                "name": bt_device.name,
                "address": bt_device.host_name.raw_name[1:-1],
                "connected": bt_device.connection_status
            })
    except OSError:
        logging.exception("got OSError when listing windows devices")

    return out


async def win_is_bt_device_connected(address):
    host_name = HostName(address)
    bt_device = await BluetoothDevice.from_host_name_async(host_name)
    return bt_device.connection_status


def win_is_dark():
    theme = UISettings()
    color_type = UIColorType.BACKGROUND
    color_value = theme.get_color_value(color_type)
    return color_value.r == 0


def tools_ready():
    if os.path.isdir(extra_tools_dir):
        return True

    response = ctypes.windll.user32.MessageBoxW(None, t("win_tools_message"), "Openfreebuds", 4)
    if response == 6:
        webbrowser.open(extra_tools_url)

    return response
