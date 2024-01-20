from openfreebuds.device import BaseDevice
from openfreebuds.logger import create_log
from version_info import VERSION

log = create_log("VirtualDevice")


class VirtualDevice(BaseDevice):
    def on_set_property(self, group: str, prop: str, value):
        log.info(f"set_property group={group}, prop={prop}, value={value}")
        self.put_property(group, prop, value)

    def close(self, lock=False):
        log.info("close")

    def connect(self):
        log.info("connect, load default props")
        self._rewrite_properties({
            "info": {
                "device_ver": "EMULATOR",
                "software_ver": VERSION,
                "device_model": "EMU"
            },
            "state": {
                "in_ear": 0
            },
            "anc": {
                "mode": "normal",
                "mode_options": "normal,cancellation,awareness",
                "level": "normal",
                "level_options": "comfort,normal,ultra",
            },
            "battery": {
                "global": 75,
                "left": 75,
                "right": 60,
                "case": 20,
                "is_charging": False
            },
            "action": {
                # DoubleTapConfigHandler
                "double_tap_left": "tap_action_off",
                "double_tap_right": "tap_action_pause",
                "double_tap_options": "tap_action_off,tap_action_pause",
                "double_tap_in_call": "tap_action_answer",
                "double_tap_in_call_options": "tap_action_off,tap_action_answer",
                # LongTapAction
                "long_tap": "tap_action_switch_anc",
                "long_tap_options": "tap_action_off,tap_action_switch_anc",
                # SwipeActionHandler
                "swipe_gesture": "tap_action_change_volume",
                "swipe_gesture_options": "tap_action_off,tap_action_change_volume",
                # PowerButtonConfigHandler
                "power_button": "tap_action_switch_device",
                "power_button_options": "tap_action_off,tap_action_switch_device",
            },
            "config": {
                "auto_pause": True,
                "sound_quality_preference": "sqp_quality",
                "sound_quality_preference_options": "sqp_quality,sqp_connectivity",
                # "equalizer_preset": "equalizer_preset_hardbass",
                # "equalizer_preset_options": "equalizer_preset_default,equalizer_preset_hardbass",
            },
            "service": {
                "supported_languages": "en-GB"
            }
        })
