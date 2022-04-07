import logging
import time

from openfreebuds import protocol_utils, event_bus
from openfreebuds.constants import spp_commands
from openfreebuds.device.spp_protocol import SppProtocolDevice
from openfreebuds.constants.events import EVENT_SPP_RECV, EVENT_SPP_WAKE_UP, EVENT_SPP_ON_WAKE_UP

log = logging.getLogger("SPPDevice")
ignored_headers = [
    [43, 16],
    [43, 4],
    [43, 22],
    [43, 24],
    [1, 31]
]


class HuaweiSPPDevice(SppProtocolDevice):
    SPP_SERVICE_UUID = "00001101-0000-1000-8000-00805f9b34fb"

    def on_init(self):
        self.send_command(spp_commands.GET_DEVICE_INFO, True)
        self.send_command(spp_commands.GET_LANGUAGE, True)
        self.send_command(spp_commands.GET_BATTERY, True)
        self.send_command(spp_commands.GET_NOISE_MODE, True)
        self.send_command(spp_commands.GET_AUTO_PAUSE, True)
        self.send_command(spp_commands.GET_TOUCHPAD_ENABLED, True)
        self.send_command(spp_commands.GET_SHORT_TAP_ACTION, True)
        self.send_command(spp_commands.GET_LONG_TAP_ACTION, True)
        self.send_command(spp_commands.GET_NOISE_CONTROL_ACTION, True)

        # Create dummy properties for service group
        self.put_property("service", "language", "_")

    def on_wake_up(self):
        self.send_command(spp_commands.GET_BATTERY)
        self.send_command(spp_commands.GET_NOISE_MODE)

    def set_property(self, group, prop, value):
        if group == "anc" and prop == "mode":
            self.send_command([43, 4, 1, 1, value])
        elif group == "config" and prop == "auto_pause":
            self.send_command([43, 16, 1, 1, value])
            self.send_command(spp_commands.GET_AUTO_PAUSE)
        elif group == "action" and prop == "double_tap_left":
            self.send_command([1, 31, 1, 1, value])
            self.send_command(spp_commands.GET_SHORT_TAP_ACTION)
        elif group == "action" and prop == "double_tap_right":
            self.send_command([1, 31, 2, 1, value])
            self.send_command(spp_commands.GET_SHORT_TAP_ACTION)
        elif group == "action" and prop == "long_tap_left":
            self.send_command([43, 22, 1, 1, value])
            self.send_command(spp_commands.GET_LONG_TAP_ACTION)
        elif group == "action" and prop == "long_tap_right":
            self.send_command([43, 22, 2, 1, value])
            self.send_command(spp_commands.GET_LONG_TAP_ACTION)
        elif group == "action" and prop == "noise_control_left":
            self.send_command([43, 24, 1, 1, value])
            self.send_command(spp_commands.GET_NOISE_CONTROL_ACTION)
        elif group == "action" and prop == "noise_control_right":
            self.send_command([43, 24, 2, 1, value])
            self.send_command(spp_commands.GET_NOISE_CONTROL_ACTION)
        elif group == "config" and prop == "touchpad_enabled":
            self.send_command([1, 44, 1, 1, value])
            self.send_command(spp_commands.GET_TOUCHPAD_ENABLED)
        elif group == "service" and prop == "language":
            data = value.encode("utf8")
            data = protocol_utils.bytes2array(data)
            self.send_command([12, 1, 1, len(data)] + data + [2, 1, 1])
        else:
            raise Exception("Can't set this prop: " + prop)

    def on_package(self, pkg):
        header = protocol_utils.bytes2array(pkg[0:2])

        if header in ignored_headers:
            log.debug("Ignored package with header: " + str(header))
            return

        if header == [1, 45]:
            self._parse_touchpad_pkg(pkg)
        elif header == [1, 8] or header == [1, 39]:
            self._parse_battery_pkg(pkg)
        elif header == [1, 32]:
            self._parse_double_tap_action(pkg)
        elif header == [1, 7]:
            self._parse_device_info(pkg)
        elif header == [43, 3]:
            self._parse_in_ear_state(pkg)
        elif header == [43, 42]:
            self._parse_noise_mode(pkg)
        elif header == [43, 17]:
            self._parse_auto_pause_mode(pkg)
        elif header == [43, 23]:
            self._parse_long_tap_action(pkg)
        elif header == [43, 25]:
            self._parse_noise_control_function(pkg)
        elif header == [12, 2]:
            self._parse_language(pkg)
        else:
            log.debug("Got undefined package, header={}, pkg={}".format(header, pkg))
            try:
                tlv = protocol_utils.parse_tlv(pkg[2:])
                for a in tlv:
                    log.debug("tlv type={}, data={}".format(a.type, a.data))
            except (protocol_utils.TLVException, ValueError):
                log.debug("Can't read as TLV pkg")

    def send_command(self, data, read=False):
        if self.sleep:
            event_bus.invoke(EVENT_SPP_WAKE_UP)
            event_bus.wait_for(EVENT_SPP_ON_WAKE_UP, timeout=1)

        self.send(protocol_utils.build_spp_bytes(data))

        if read:
            t = time.time()
            event_bus.wait_for(EVENT_SPP_RECV, timeout=1)
            if time.time() - t > 0.9:
                log.warning("Too long read wait, maybe command is ignored")

    def _parse_language(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        supported = contents.find_by_type(3)
        if supported.length > 1:
            self.put_property("service", "supported_languages", supported.get_string())

    def _parse_battery_pkg(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        level = contents.find_by_type(2)
        if level.length > 0:
            self.put_group("battery", {
                "left": level.data[0],
                "right": level.data[1],
                "case": level.data[2]
            })

    def _parse_in_ear_state(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_types([8, 9])
        if row.length == 1:
            self.put_property("state", "in_ear", row.data[0] == 1)

    def _parse_noise_mode(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_type(1)
        if row.length == 2:
            self.put_property("anc", "mode", row.data[1])

    def _parse_touchpad_pkg(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_type(1)
        if row.length == 1:
            self.put_property("config", "touchpad_enabled", row.data[0])

    def _parse_noise_control_function(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action", "noise_control_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action", "noise_control_right", right.data[0])

    def _parse_auto_pause_mode(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_type(1)
        if row.length == 1:
            self.put_property("config", "auto_pause", row.data[0])

    def _parse_long_tap_action(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action", "long_tap_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action", "long_tap_right", right.data[0])

    def _parse_double_tap_action(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action", "double_tap_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action", "double_tap_right", right.data[0])

    def _parse_device_info(self, pkg):
        descriptor = {
            "device_ver": 3,
            "software_ver": 7,
            "serial_number": 9,
            "device_model": 10,
            "ota_version": 15
        }

        contents = protocol_utils.parse_tlv(pkg[2:])
        out = {}

        for key in descriptor:
            row = contents.find_by_type(descriptor[key])
            if row.length > 0:
                out[key] = row.get_string()

        self.put_group("info", out)
