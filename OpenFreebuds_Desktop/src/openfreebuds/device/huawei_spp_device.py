import logging
import time
from array import array

from openfreebuds import protocol_utils, event_bus
from openfreebuds.constants import spp_commands
from openfreebuds.device.base import with_no_prop_changed_event
from openfreebuds.device.spp_protocol import SppProtocolDevice
from openfreebuds.constants.events import EVENT_SPP_RECV, EVENT_SPP_WAKE_UP, EVENT_SPP_ON_WAKE_UP

log = logging.getLogger("SPPDevice")


class HuaweiSPPDevice(SppProtocolDevice):
    SPP_SERVICE_UUID = "00001101-0000-1000-8000-00805f9b34fb"

    HAS_SERVICE_LANGUAGE_PROP = False
    IGNORE_HEADERS = []
    WAKE_UP_READ_COMMANDS = []
    INIT_READ_COMMANDS = []

    @with_no_prop_changed_event
    def on_init(self):
        # Do initial data read
        for pkg in self.INIT_READ_COMMANDS:
            self.send_command(pkg, True)

        # Create dummy properties for service group
        if self.HAS_SERVICE_LANGUAGE_PROP:
            self.put_property("service", "language", "_")

    @with_no_prop_changed_event
    def on_wake_up(self):
        for pkg in self.WAKE_UP_READ_COMMANDS:
            self.send_command(pkg, True)

    def __init__(self, address):
        super().__init__(address)

        self.bind_on_package([b'\x0c\x02'], self._parse_language)
        self.bind_on_package([b'\x01-'], self._parse_touchpad_enabled)
        self.bind_on_package([b'\x01\x08', b'\x01\''], self._parse_battery_pkg)
        self.bind_on_package([b'\x01 '], self._parse_double_tap_action)
        self.bind_on_package([b'\x01\x07'], self._parse_device_info)
        self.bind_on_package([b'+\x03'], self._parse_in_ear_state)
        self.bind_on_package([b'+*'], self._parse_noise_mode)
        self.bind_on_package([b'+\x11'], self._parse_auto_pause_mode)
        self.bind_on_package([b'+\x17'], self._parse_long_tap_action)
        self.bind_on_package([b'+\x19'], self._parse_noise_control_function)

        self.bind_set_property("service", "language", self._set_language)
        self.bind_set_property("anc", "mode", self._set_noise_mode)
        self.bind_set_property("config", "touchpad_enabled", self._set_touchpad_enabled)
        self.bind_set_property("config", "auto_pause", self._set_auto_pause_mode)
        self.bind_set_property("action", "long_tap_left", self._set_long_tab_action_left)
        self.bind_set_property("action", "long_tap_right", self._set_long_tab_action_right)
        self.bind_set_property("action", "double_tap_left", self._set_double_tap_action_left)
        self.bind_set_property("action", "double_tap_right", self._set_double_tap_action_right)
        self.bind_set_property("action", "noise_control_left", self._set_noise_control_function_left)
        self.bind_set_property("action", "noise_control_right", self._set_noise_control_function_right)

    def on_package(self, pkg):
        pkg = array("b", pkg)
        header = pkg[0:2].tobytes()

        # log.debug("got pkg, pkg={}".format(pkg))

        if header in self.recv_handlers:
            self.recv_handlers[header](pkg)
        elif header not in self.IGNORE_HEADERS:
            log.debug("Got undefined package, header={}, pkg={}".format(header, pkg))
            try:
                tlv = protocol_utils.parse_tlv(pkg[2:])
                for a in tlv:
                    log.debug("tlv type={}, data={}".format(a.type, a.data))
            except (protocol_utils.TLVException, ValueError):
                log.debug("Can't read as TLV pkg")

    def send_command(self, data: array, read=False):
        if self.sleep:
            event_bus.invoke(EVENT_SPP_WAKE_UP)
            event_bus.wait_for(EVENT_SPP_ON_WAKE_UP, timeout=1)

        header = b"Z" + (len(data) + 1).to_bytes(2, byteorder="big") + b"\x00"
        package = array("b", header)
        package.extend(data)

        checksum = protocol_utils.crc16char(package)
        package.extend(checksum)

        self.send(package.tobytes())

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

    def _set_language(self, value: str):
        lang_bytes = value.encode("utf8")

        package = array("b", spp_commands.SET_LANGUAGE)
        for i in range(len(lang_bytes)):
            package[4 + i] = lang_bytes[i]

        self.send_command(package)

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

    def _set_noise_mode(self, value: int):
        package = array("b", spp_commands.SET_NOISE_MODE)
        package[4] = value
        self.send_command(package)

    def _parse_touchpad_enabled(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_type(1)
        if row.length == 1:
            self.put_property("config", "touchpad_enabled", row.data[0])

    def _set_touchpad_enabled(self, value: int):
        package = array("b", spp_commands.SET_TOUCHPAD_ENABLED)
        package[4] = value

        self.send_command(package)
        self.send_command(spp_commands.GET_TOUCHPAD_ENABLED)

    def _parse_noise_control_function(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action", "noise_control_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action", "noise_control_right", right.data[0])

    def _set_noise_control_function_left(self, value: int):
        package = array("b", spp_commands.SET_NOISE_CONTROL_ACTION)
        package[2] = 1
        package[4] = value

        self.send_command(package)
        self.send_command(spp_commands.GET_NOISE_CONTROL_ACTION)

    def _set_noise_control_function_right(self, value: int):
        package = array("b", spp_commands.SET_NOISE_CONTROL_ACTION)
        package[2] = 2
        package[4] = value

        self.send_command(package)
        self.send_command(spp_commands.GET_NOISE_CONTROL_ACTION)

    def _parse_auto_pause_mode(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        row = contents.find_by_type(1)
        if row.length == 1:
            self.put_property("config", "auto_pause", row.data[0])

    def _set_auto_pause_mode(self, value: int):
        package = array("b", spp_commands.SET_AUTO_PAUSE)
        package[4] = value

        self.send_command(package)
        self.send_command(spp_commands.GET_AUTO_PAUSE)

    def _parse_long_tap_action(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action", "long_tap_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action", "long_tap_right", right.data[0])

    def _set_long_tab_action_left(self, value: int):
        package = array("b", spp_commands.SET_LONG_TAP_ACTION)
        package[2] = 1
        package[4] = value
        self.send_command(package)
        self.send_command(spp_commands.GET_LONG_TAP_ACTION)

    def _set_long_tab_action_right(self, value: int):
        package = array("b", spp_commands.SET_LONG_TAP_ACTION)
        package[2] = 2
        package[4] = value
        self.send_command(package)
        self.send_command(spp_commands.GET_LONG_TAP_ACTION)

    def _parse_double_tap_action(self, pkg):
        contents = protocol_utils.parse_tlv(pkg[2:])

        left = contents.find_by_type(1)
        if left.length == 1:
            self.put_property("action", "double_tap_left", left.data[0])

        right = contents.find_by_type(2)
        if right.length == 1:
            self.put_property("action", "double_tap_right", right.data[0])

    def _set_double_tap_action_left(self, value: int):
        package = array("b", spp_commands.SET_DOUBLE_TAP_ACTION)
        package[2] = 1
        package[4] = value

        self.send_command(package)
        self.send_command(spp_commands.GET_SHORT_TAP_ACTION)

    def _set_double_tap_action_right(self, value: int):
        package = array("b", [1, 31, -1, 1, -1])
        package[2] = 2
        package[4] = value

        self.send_command(package)
        self.send_command(spp_commands.GET_SHORT_TAP_ACTION)

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
