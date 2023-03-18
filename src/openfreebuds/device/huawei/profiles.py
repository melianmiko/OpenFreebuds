from openfreebuds.device.huawei.generic.spp_device import GenericHuaweiSppDevice

from openfreebuds.device.huawei.spp_handlers.anc_handlers import *
from openfreebuds.device.huawei.spp_handlers.base_handlers import *
from openfreebuds.device.huawei.spp_handlers.gesture_config_handlers import *
from openfreebuds.device.huawei.spp_handlers.tws_handlers import *


class FreeLaceProDevice(GenericHuaweiSppDevice):
    handlers = [
        Drop2b03Handler(),
        DeviceInfoHandler(),
        BatteryHandler(),
        ProAncHandler(),
        PowerButtonConfigHandler(),
        LongTapAction(),
    ]


class FreeBuds4iDevice(GenericHuaweiSppDevice):
    handlers = [
        DropLogsHandler(),
        DeviceInfoHandler(),
        TwsInEarHandler(),
        SimpleAncHandler(),
        BatteryHandler(),
        # TouchpadConfigHandler(),
        DoubleTapConfigHandler(),
        SplitLongTapActionConfigHandler(),
        TwsAutoPauseHandler(),
        VoiceLanguageHandler(),
    ]
