from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler import *


class OfbDriverHuawei5(OfbDriverHuaweiGeneric):
    """HUAWEI FreeBuds 5 (modelId 000141 / productId ZAAB / internal name Honey)

    HUAWEI FreeBuds Lipstick 2 (modelId 000151 / productId ZAAJ / internal name
    Diva) is registered as an alias of this driver: its official command pages
    match FreeBuds 5 and differ only in shell/color assets and the custom-EQ
    display flag.
    
    Capability sources:
    - Huawei AI Life 2.0.7.321 assets/config/device_whitelist.json -> modelId 000141, deviceName HUAWEI FreeBuds 5, btDevNameReg contains Honey/HONEY
    - assets/000141.json -> hardwareAttributes: dualConnect, l2hc; softwareFeatures: eqAdjust, highQuality, spatialAudio. spatialAudio here means HD spatial audio available only with Huawei phones, not the standalone spatial audio available to all devices; singleValueConfigMap.wearingMode: halfInEar
    - assets/config/config_ZAAB.json -> findHeadset: 2 (supported); battery.isSupportBox / isSupportDoubleEar: true; noiseControl: simple noise control on, advanced noise control off, two modes (normal / cancellation), ANC level on, ANC AI scene on, sub-human voice off; soundQuality: custom EQ, code, game low latency
    - assets/touchsetting/config_zaab.json -> double tap (including in call), triple tap, independent long-press per ear, swipe up/down
    - assets/feature_config.json -> isDualConnect=true, dora_config=true
    """

    def __init__(self, address):
        super().__init__(address)
        self._spp_service_port = 1
        self.handlers = [
            OfbHuaweiInfoHandler(),
            OfbHuaweiStateInEarHandler(),
            OfbHuaweiBatteryHandler(),
            OfbHuaweiAncHandler(
                w_cancel_lvl=True,
                w_cancel_dynamic=True,
                w_awareness=False,
            ),
            OfbHuaweiActionDoubleTapHandler(w_in_call=True),
            OfbHuaweiActionTripleTapHandler(),
            OfbHuaweiActionLongTapSplitHandler(w_right=True, w_in_call=True),
            OfbHuaweiActionSwipeGestureHandler(),
            OfbHuaweiConfigAutoPauseHandler(),
            OfnHuaweiSoundQualityPreferenceHandler(),
            OfbHuaweiLowLatencyPreferenceHandler(),
            OfbHuaweiEqualizerPresetHandler(
                w_presets={
                    1: "default",
                    2: "hardbass",
                    3: "treble",
                    9: "voices",
                },
                w_custom=True,
                w_custom_rows=10,
                w_custom_max_count=3,
            ),
            OfbHuaweiVoiceLanguageHandler(),
            OfbHuaweiDualConnectHandler(),
        ]
