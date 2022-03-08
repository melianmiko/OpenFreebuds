import logging

from openfreebuds import protocol_utils
from openfreebuds.spp.base import BaseSPPDevice

log = logging.getLogger("SPPDevice")


def create(address):
    return SPPDevice(address)


class SPPCommands:
    GET_DEVICE_INFO = [1, 7, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0,
                       7, 0, 8, 0, 9, 0, 10, 0, 11, 0,
                       12, 0, 15, 0, 25, 0]
    GET_BATTERY = [1, 8, 1, 0, 2, 0, 3, 0]
    GET_NOISE_MODE = [43, 42, 1, 0]
    GET_AUTO_PAUSE = [43, 17, 1, 0]
    GET_LONG_TAP_ACTION = [43, 23, 1, 0, 2, 0]
    GET_SHORT_TAP_ACTION = [1, 32, 1, 0, 2, 0]
    GET_LANGUAGE = [12, 2, 1, 0, 3, 0]
    GET_NOISE_CONTROL_ACTION = [43, 25, 1, 0, 2, 0]
    TEST = [43, 56, 1, 0]


class SPPDevice(BaseSPPDevice):
    def __init__(self, address):
        super().__init__(address)

    def on_init(self):
        self.send_command(SPPCommands.GET_DEVICE_INFO, True)
        self.send_command(SPPCommands.GET_BATTERY, True)
        self.send_command(SPPCommands.GET_NOISE_MODE, True)
        self.send_command(SPPCommands.GET_AUTO_PAUSE, True)
        self.send_command(SPPCommands.GET_LONG_TAP_ACTION, True)
        self.send_command(SPPCommands.GET_SHORT_TAP_ACTION, True)
        self.send_command(SPPCommands.GET_LANGUAGE, True)
        self.send_command(SPPCommands.GET_NOISE_CONTROL_ACTION, True)
        self.send_command(SPPCommands.TEST, True)

    def set_property(self, prop, value):
        if prop == "noise_mode" and value in [0, 1, 2]:
            self.send_command([43, 4, 1, 1, value])
        elif prop == "auto_pause" and value in [0, 1]:
            self.send_command([43, 16, 1, 1, value])
            self.send_command(SPPCommands.GET_AUTO_PAUSE)
        elif prop == "action_double_tap_left":
            self.send_command([1, 31, 1, 1, value])
            self.send_command(SPPCommands.GET_SHORT_TAP_ACTION)
        elif prop == "action_double_tap_right":
            self.send_command([1, 31, 2, 1, value])
            self.send_command(SPPCommands.GET_SHORT_TAP_ACTION)
        elif prop == "action_long_tap_left":
            self.send_command([43, 22, 1, 1, value])
            self.send_command(SPPCommands.GET_LONG_TAP_ACTION)
        elif prop == "action_long_tap_right":
            self.send_command([43, 22, 2, 1, value])
            self.send_command(SPPCommands.GET_LONG_TAP_ACTION)
        elif prop == "action_noise_control_left":
            self.send_command([43, 24, 1, 1, value])
            self.send_command(SPPCommands.GET_NOISE_CONTROL_ACTION)
        elif prop == "action_noise_control_right":
            self.send_command([43, 24, 2, 1, value])
            self.send_command(SPPCommands.GET_NOISE_CONTROL_ACTION)
        elif prop == "language":
            data = value.encode("utf8")
            data = protocol_utils.bytes2array(data)
            self.send_command([12, 1, 1, len(data)] + data + [2, 1, 1])
        else:
            raise Exception("Can't set this prop: " + prop)

    def on_package(self, pkg):
        header = protocol_utils.bytes2array(pkg[0:2])
        if header == [1, 8] or header == [1, 39]:
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
                    logging.debug("tlv type={}, data={}".format(a.type, a.data))
            except (protocol_utils.TLVException, ValueError):
                log.debug("Can't read as TLV pkg")

    def _parse_language(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        supported = contents.find_by_type(3)
        if supported.length > 1:
            self.put_property("supported_languages", supported.get_string())

    def _parse_battery_pkg(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        level = contents.find_by_type(2)
        if level.length > 0:
            self.put_property("battery_left", level.data[0])
            self.put_property("battery_right", level.data[1])
            self.put_property("battery_case", level.data[2])

    def _parse_in_ear_state(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_types([8, 9])
        if row.length == 1:
            self.put_property("is_headphone_in", row.data[0] == 1)

    def _parse_noise_mode(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_type(1)
        if row.length == 2:
            self.put_property("noise_mode", row.data[1])

    def _parse_noise_control_function(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action_noise_control_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action_noise_control_right", right.data[0])

    def _parse_auto_pause_mode(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_type(1)
        if row.length == 1:
            self.put_property("auto_pause", row.data[0])

    def _parse_long_tap_action(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action_long_tap_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action_long_tap_right", right.data[0])

    def _parse_double_tap_action(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action_double_tap_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action_double_tap_right", right.data[0])

    def _parse_device_info(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])
        descriptor = {
            "device_ver": 3,
            "software_ver": 7,
            "serial_number": 9,
            "device_model": 10,
            "ota_version": 15
        }

        for key in descriptor:
            row = contents.find_by_type(descriptor[key])
            if row.length > 0:
                self.put_property(key, row.get_string())
