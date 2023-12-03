from openfreebuds.device.huawei.generic.spp_device import GenericHuaweiSppDevice
from openfreebuds.device.huawei.spp_handlers.anc_change import AncChangeDetectionHandler
from openfreebuds.device.huawei.spp_handlers.anc_pro import ProAncHandler
from openfreebuds.device.huawei.spp_handlers.anc_simple import SimpleAncHandler
from openfreebuds.device.huawei.spp_handlers.battery import BatteryHandler
from openfreebuds.device.huawei.spp_handlers.device_info import DeviceInfoHandler
from openfreebuds.device.huawei.spp_handlers.drop import DropLogsHandler
from openfreebuds.device.huawei.spp_handlers.gesture_double import DoubleTapConfigHandler
from openfreebuds.device.huawei.spp_handlers.gesture_long import LongTapAction
from openfreebuds.device.huawei.spp_handlers.gesture_long_separate import SplitLongTapActionConfigHandler
from openfreebuds.device.huawei.spp_handlers.gesture_power import PowerButtonConfigHandler
from openfreebuds.device.huawei.spp_handlers.tws_auto_pause import TwsAutoPauseHandler
from openfreebuds.device.huawei.spp_handlers.tws_in_ear import TwsInEarHandler
from openfreebuds.device.huawei.spp_handlers.voice_language import VoiceLanguageHandler


class FreeLaceProDevice(GenericHuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)

        # Add cooldown to prevent device hang
        self.spp_connect_sleep = 1

        self.handlers = [
            # Drop2b03Handler(),
            DeviceInfoHandler(),
            BatteryHandler(),
            ProAncHandler(),
            AncChangeDetectionHandler(),
            PowerButtonConfigHandler(),
            LongTapAction(),
        ]


class FreeBuds4iDevice(GenericHuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            DropLogsHandler(),
            DeviceInfoHandler(),
            TwsInEarHandler(),
            SimpleAncHandler(),
            BatteryHandler(),
            # TouchpadConfigHandler(),
            DoubleTapConfigHandler(),
            SplitLongTapActionConfigHandler(False),
            TwsAutoPauseHandler(),
            VoiceLanguageHandler(),
        ]


class FreeBudsSEDevice(GenericHuaweiSppDevice):
    def __init__(self, address):
        super().__init__(address)
        self.handlers = [
            DropLogsHandler(),
            DeviceInfoHandler(),
            BatteryHandler(),
            DoubleTapConfigHandler(),
        ]
