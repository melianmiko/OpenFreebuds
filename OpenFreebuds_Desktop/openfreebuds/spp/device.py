from openfreebuds import protocol_utils
from openfreebuds.spp.base import BaseSPPDevice


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
        elif prop == "action_long_tap_enabled":
            raise "TODO: Implement me!"
        else:
            raise "Can't set this prop: " + prop

    def on_package(self, pkg):
        if pkg[0] == 1:
            if pkg[1] == 8 or pkg[1] == 39:
                self._parse_battery_pkg(pkg)
            elif pkg[1] == 32:
                self._parse_double_tap_action(pkg)
            elif pkg[1] == 7:
                self._parse_device_info(pkg)
        elif pkg[0] == 43:
            if pkg[1] == 3:
                self._parse_in_ear_state(pkg)
            elif pkg[1] == 42:
                self._parse_noise_mode(pkg)
            elif pkg[1] == 17:
                self._parse_auto_pause_mode(pkg)
            elif pkg[1] == 23:
                self._parse_long_tap_enabled(pkg)

    def _parse_battery_pkg(self, pkg):
        parts = protocol_utils.parse_tlv(pkg[2:])
        for a in parts:
            if a[0] == 2:
                data = a[1]
                self.put_property("battery_left", data[0])
                self.put_property("battery_right", data[1])
                self.put_property("battery_case", data[2])

    def _parse_in_ear_state(self, pkg):
        parts = protocol_utils.parse_tlv(pkg[2:])

        for data in parts:
            if data[0] == 8 or data[0] == 9:
                self.put_property("is_headphone_in", data[1][0] == 1)
                return

    def _parse_noise_mode(self, pkg):
        parts = protocol_utils.parse_tlv(pkg[2:])

        for a in parts:
            if a[0] == 1 and len(a[1]) == 2:
                self.put_property("noise_mode", a[1][1])
                return

    def _parse_auto_pause_mode(self, pkg):
        parts = protocol_utils.parse_tlv(pkg[2:])

        for a in parts:
            if a[0] == 1 and len(a[1]) == 1:
                self.put_property("auto_pause", a[1][0])
                return

    def _parse_long_tap_enabled(self, pkg):
        parts = protocol_utils.parse_tlv(pkg[2:])

        for a in parts:
            if a[0] == 1 and len(a[1]) == 1:
                self.put_property("action_long_tap_enabled", a[1][0] == 10)
                return

    def _parse_double_tap_action(self, pkg):
        parts = protocol_utils.parse_tlv(pkg[2:])

        for a in parts:
            if a[0] == 1 and len(a[1]) == 1:
                self.put_property("action_double_tap_left", a[1][0])
            elif a[0] == 2 and len(a[1]) == 1:
                self.put_property("action_double_tap_right", a[1][0])

    def _parse_device_info(self, pkg):
        parts = protocol_utils.parse_tlv(pkg[2:])

        for a in parts:
            if a[0] == 3:
                self.put_property("device_ver", str(a[2], "utf8"))
            elif a[0] == 7:
                self.put_property("software_ver", str(a[2], "utf8"))
            elif a[0] == 9:
                self.put_property("serial_number", str(a[2], "utf8"))
            elif a[0] == 10:
                self.put_property("device_model", str(a[2], "utf8"))
            elif a[0] == 15:
                self.put_property("ota_version", str(a[2], "utf8"))
