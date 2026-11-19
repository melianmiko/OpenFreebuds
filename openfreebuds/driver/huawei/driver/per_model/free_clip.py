from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import (
    OfbHuaweiActionDoubleTapHandler,
    OfbHuaweiActionTripleTapHandler,
    OfbHuaweiAncHandler,
    OfbHuaweiBatteryHandler,
    OfbHuaweiBoxToneHandler,
    OfbHuaweiConfigAutoPauseHandler,
    OfbHuaweiDropReminderHandler,
    OfbHuaweiDualConnectHandler,
    OfbHuaweiEqualizerPresetHandler,
    OfbHuaweiHeadControlHandler,
    OfbHuaweiInfoHandler,
    OfbHuaweiLowLatencyPreferenceHandler,
    OfbHuaweiStateInEarHandler,
    OfbHuaweiVoiceLanguageHandler,
    OfnHuaweiSoundQualityPreferenceHandler,
)


class OfbDriverHuaweiFreeClip(OfbDriverHuaweiGeneric):
    """HUAWEI FreeClip (1st gen, modelId 00014B / productId ZAAI / Dove).

    This driver is intentionally standalone. It previously inherited the Pro 3
    driver and removed handlers at runtime; that made a Pro 3 capability change
    silently affect FreeClip. Keep the explicit list below instead.

    Capability sources:
    - assets/config/config_ZAAI.json: ANC with level/dynamic/voice boost, EQ,
      auto-pause, dual-connect, voice language, low latency.
    - assets/touchsetting/config_zaai.json: double/triple tap only. There is no
      light-hold, long-press or swipe page.
    - assets config: other charging-case tones exist, but no writable lid-open
      tone page, so box tone stays master-only.
    - Official lab UI: click-and-hold and five-tap volume modes exist for
      00014B, but OpenFreebuds does not model them yet.
    """

    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiAncHandler(
                w_cancel_lvl=True,
                w_cancel_dynamic=True,
                w_voice_boost=True,
            ),
            OfbHuaweiBatteryHandler(),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiEqualizerPresetHandler(
                w_presets={
                    5: "default",
                    1: "hardbass",
                    2: "treble",
                    9: "voice",
                },
                w_custom=True,
            ),
            OfbHuaweiConfigAutoPauseHandler(),
            OfbHuaweiDualConnectHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),
            OfbHuaweiBoxToneHandler(w_lid_tone=False),
            OfbHuaweiActionDoubleTapHandler(
                w_in_call=True,
                w_read_in_call=True,
            ),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiHeadControlHandler(),
            OfbHuaweiDropReminderHandler(),
        ]
