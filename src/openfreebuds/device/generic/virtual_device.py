import logging

from openfreebuds.device import BaseDevice
from version_info import VERSION

log = logging.getLogger("VirtualDevice")


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
                "mode": 0,
                "level": 0
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
                # SplitLongTapActionConfigHandler (with_right=False)
                "long_tap_left": "tap_action_switch_anc",
                "long_tap_options": "tap_action_off,tap_action_switch_anc",
                "noise_control_left": "noise_control_off_on_aw",
                "noise_control_options": "noise_control_off_on,noise_control_off_on_aw"
            },
            "config": {
                "auto_pause": True
            },
            "service": {
                "supported_languages": "en-GB"
            }
        })
