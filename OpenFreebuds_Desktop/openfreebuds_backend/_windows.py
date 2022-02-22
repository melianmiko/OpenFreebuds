import ctypes
import logging
import asyncio
import pystray._win32
import pystray._base

# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.devices.bluetooth import BluetoothDevice
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.networking import HostName
# noinspection PyUnresolvedReferences,PyPackageRequirements
from winsdk.windows.ui.viewmanagement import UISettings, UIColorType

# Yes, this isn't good practise, but this reduces count
# of imported package and force set backend to app indicator
Menu = pystray._base.Menu
MenuItem = pystray._base.MenuItem
TrayIcon = pystray._win32.Icon


UI_RESULT_NO = 6
UI_RESULT_YES = 7

log = logging.getLogger("WindowsBackend")


def bt_is_connected(address):
    return asyncio.run(_is_device_connected(address))


def bt_device_exists(address):
    devices = bt_list_devices()

    for a in devices:
        if a["address"] == address:
            return True

    return False


def bt_list_devices():
    return asyncio.run(_list_paired())


def show_message(message, window_title=""):
    ctypes.windll.user32.MessageBoxW(None, message, window_title, 0)


def ask_question(message, window_title=""):
    return ctypes.windll.user32.MessageBoxW(None, message, window_title, 4)


def is_dark_theme():
    theme = UISettings()
    color_type = UIColorType.BACKGROUND
    color_value = theme.get_color_value(color_type)
    return color_value.r == 0


async def _list_paired():
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


async def _is_device_connected(address):
    host_name = HostName(address)
    bt_device = await BluetoothDevice.from_host_name_async(host_name)
    return bt_device.connection_status
