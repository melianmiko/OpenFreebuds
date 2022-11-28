from openfreebuds.constants import spp_commands
from openfreebuds.device.huawei_spp_device import HuaweiSPPDevice


class FreeBuds4iDevice(HuaweiSPPDevice):
    HAS_SERVICE_LANGUAGE_PROP = True
    IGNORE_HEADERS = [
        b'+\x10',
        b'+\x04',
        b'+\x16',
        b'+\x18',
        b'\x01\x1f'
    ]
    WAKE_UP_READ_COMMANDS = [
        spp_commands.GET_BATTERY,
        spp_commands.GET_NOISE_MODE
    ]
    INIT_READ_COMMANDS = [
        spp_commands.GET_DEVICE_INFO,
        spp_commands.GET_LANGUAGE,
        spp_commands.GET_BATTERY,
        spp_commands.GET_NOISE_MODE,
        spp_commands.GET_AUTO_PAUSE,
        spp_commands.GET_TOUCHPAD_ENABLED,
        spp_commands.GET_SHORT_TAP_ACTION,
        spp_commands.GET_LONG_TAP_ACTION,
        spp_commands.GET_NOISE_CONTROL_ACTION
    ]
