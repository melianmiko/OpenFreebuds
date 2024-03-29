from openfreebuds.device.huawei.generic.spp_device import GenericHuaweiSppDevice
from openfreebuds.device.huawei.spp_handlers.anc_control import AncSettingHandler
from openfreebuds.device.huawei.spp_handlers.battery import BatteryHandler
from openfreebuds.device.huawei.spp_handlers.device_info import DeviceInfoHandler
from openfreebuds.device.huawei.spp_handlers.drop import DropLogsHandler
from openfreebuds.device.huawei.spp_handlers.gesture_double import DoubleTapConfigHandler
from openfreebuds.device.huawei.spp_handlers.gesture_long_separate import SplitLongTapActionConfigHandler
from openfreebuds.device.huawei.spp_handlers.tws_auto_pause import TwsAutoPauseHandler
from openfreebuds.device.huawei.spp_handlers.tws_in_ear import TwsInEarHandler
from openfreebuds.device.huawei.spp_handlers.voice_language import VoiceLanguageHandler


class FreeBuds4iDevice(GenericHuaweiSppDevice):
    """
    HUAWEI FreeBuds 4i
    """
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            DropLogsHandler(),
            DeviceInfoHandler(),
            TwsInEarHandler(),
            AncSettingHandler(),
            BatteryHandler(),
            # TouchpadConfigHandler(),
            DoubleTapConfigHandler(),
            SplitLongTapActionConfigHandler(),
            TwsAutoPauseHandler(),
            VoiceLanguageHandler(),
        ]
