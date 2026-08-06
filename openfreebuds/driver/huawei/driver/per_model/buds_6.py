from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuawei6(OfbDriverHuaweiGeneric):
    """
    HUAWEI FreeBuds 6

    Open-fit (half-in-ear) dual-driver earbuds, device model BTFT0020.

    Handler set is based on replies captured from real hardware
    (see docs/devices/HUAWEI_FreeBuds_6.md).
    """

    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiConfigAutoPauseHandler(),

            # Open-fit ANC. Device replies to 2b2a with a 2-byte param,
            # so mode switching works. Availability of cancellation levels
            # is still unconfirmed.
            OfbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True),

            # Gestures. Double tap reports in-call options (param 4/6),
            # long tap reports both earbuds plus in-call.
            OfbHuaweiActionDoubleTapHandler(w_in_call=True),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiActionLongTapSplitHandler(w_right=True, w_in_call=True),
            OfbHuaweiActionSwipeGestureHandler(),

            # Equalizer. Built-in preset ids are read from the device
            # (0, 2, 3, 9, 11, 12) instead of being hardcoded, because this
            # model has no preset 1 and adds two presets unknown to the
            # shared preset table.
            OfbHuaweiEqualizerPresetHandler(w_custom=True),

            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiDualConnectHandler(),

            # Not supported by this model:
            # - low latency (2b6c) replies with error param 127
            #
            # Not implemented (no SPP research data available):
            # - head gestures (nod/shake to answer or reject a call)
            # - spatial / room audio
            # - adaptive volume in noisy environments
        ]
