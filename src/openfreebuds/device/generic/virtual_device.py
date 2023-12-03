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
                "double_tap_left": -1,
                "double_tap_right": -1,
                "long_tap_left": -1,
                "long_tap_right": -1,
                "noise_control_left": 2,
                "noise_control_right": 2,
            },
            "config": {
                "auto_pause": True
            },
            "service": {
                "supported_languages": "en-GB"
            }
        })
