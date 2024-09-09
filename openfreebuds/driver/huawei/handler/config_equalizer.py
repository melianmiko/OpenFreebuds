import json
from typing import Optional

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import OfbNotSupportedError, OfbTooManyItemsError
from openfreebuds.utils import reverse_dict
from openfreebuds.utils.logger import create_logger

KNOWN_BUILT_IN_PRESETS = {
    1: "equalizer_preset_default",
    2: "equalizer_preset_hardbass",
    3: "equalizer_preset_treble",
    9: "equalizer_preset_voices",
}

log = create_logger("OfbHuaweiEqualizerPresetHandler")


class OfbHuaweiEqualizerPresetHandler(OfbDriverHandlerHuawei):
    """
    Built-in equalizer settings handler (5i)
    """
    handler_id = "config_eq"
    properties = [
        ("sound", "equalizer_preset"),
        ("sound", "equalizer_rows"),
    ]
    commands = [b"\x2b\x4a"]
    ignore_commands = [b"\x2b\x49"]

    def __init__(
            self,
            w_presets: Optional[dict[int, str]] = None,
            w_custom: bool = False,
            w_custom_rows: int = 10,
            w_custom_max_count: int = 3,
    ):
        self.w_custom: bool = w_custom
        self.w_custom_rows = w_custom_rows
        self.w_custom_max_count = w_custom_max_count
        self.w_options_predefined: bool = w_presets is not None

        self.custom_preset_values: dict[int, bytes] = {}
        self.options: Optional[dict[int, str]] = None
        if w_presets:
            self.options = {i: f"equalizer_preset_{name}" for i, name in w_presets.items()}

    async def on_init(self):
        resp = await self.driver.send_package(
            HuaweiSppPackage.read_rq(b"\x2b\x4a", [1, 2, 3, 4, 5, 6, 7, 8])
        )
        await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
        if prop == "equalizer_preset":
            return await self._set_current_mode(value)
        elif prop == "equalizer_rows" and value == "null":
            return await self._delete_current_mode()
        elif prop == "equalizer_rows":
            return await self._change_current_mode(value)

        raise OfbNotSupportedError("Impossible error")

    async def _change_current_mode(self, value: str):
        mode_str = await self.driver.get_property("sound", "equalizer_preset", None)
        mode_id = reverse_dict(self.options).get(mode_str)
        if mode_id is None:
            return

        data = b"".join([x.to_bytes(1, byteorder="big", signed=True) for x in json.loads(value)])
        log.info(f"Will replace id={mode_id}, label={mode_str} with data={data}")

        pkg = HuaweiSppPackage.change_rq(
            b"\x2b\x49",
            _build_payload(mode_id, mode_str, data, 1)
        )
        await self.driver.send_package(pkg)
        await self.driver.put_property("sound", "equalizer_rows", value)

    async def _delete_current_mode(self):
        mode_str = await self.driver.get_property("sound", "equalizer_preset", None)
        mode_id = reverse_dict(self.options).get(mode_str)
        if mode_id is None:
            return

        data = self.custom_preset_values[mode_id]
        log.info(f"Delete id={mode_id}, label={mode_str}, data={data}")

        pkg = HuaweiSppPackage.change_rq(
            b"\x2b\x49",
            _build_payload(mode_id, mode_str, data, 2)
        )
        await self.driver.send_package(pkg)
        await self.on_init()

    async def _set_current_mode(self, mode_str):
        mode_id = reverse_dict(self.options).get(mode_str)

        # New mode creation
        if mode_id is None:
            if not self.w_custom:
                raise OfbNotSupportedError("Device didn't support custom equalizer presets")
            if len(self.custom_preset_values.keys()) >= self.w_custom_max_count:
                raise OfbTooManyItemsError()

            mode_id = 100
            while mode_id in self.custom_preset_values:
                mode_id += 1
            data = b"\x00" * self.w_custom_rows

            current_mode = await self.driver.get_property("sound", "equalizer_preset", None)
            current_mode_id = reverse_dict(self.options).get(current_mode)
            if current_mode_id in self.custom_preset_values:
                data = self.custom_preset_values[current_mode_id]

            self.custom_preset_values[mode_id] = data
            log.info(f"Will create new preset id={mode_id}, data={data}")

        if mode_id in self.custom_preset_values:
            # Is custom mode, use advanced payload
            data = self.custom_preset_values[mode_id]
            pkg = HuaweiSppPackage.change_rq(
                b"\x2b\x49",
                _build_payload(mode_id, mode_str, data, 1)
            )
        else:
            # Is built'in mode
            pkg = HuaweiSppPackage.change_rq(
                b"\x2b\x49",
                [(1, mode_id)]
            )

        await self.driver.send_package(pkg)
        await self.on_init()

    async def on_package(self, package: HuaweiSppPackage):
        new_props = {"equalizer_rows": None}
        available_modes = package.find_param(3)
        if not self.w_options_predefined and len(available_modes) > 0:
            self.options = {i: KNOWN_BUILT_IN_PRESETS.get(i, f"preset_{i}") for i in available_modes}
            # log.info(f"Read built-in options {self.options}")

        custom_modes = package.find_param(8)
        if self.w_custom and len(custom_modes) > 0:
            offset = 0
            self.custom_preset_values = {}
            while offset < len(custom_modes):
                mode_id, mode_label, mode_data = _parse_custom_mode(custom_modes[offset:offset + 36])
                self.custom_preset_values[mode_id] = mode_data
                self.options[mode_id] = mode_label
                # log.info(f"Read custom mode id={mode_id}, label={mode_label}, data={mode_data}")
                offset += 36

        new_props["equalizer_preset_options"] = ",".join(self.options.values())

        current_mode = package.find_param(2)
        if len(current_mode) == 1:
            current_mode = int.from_bytes(current_mode, byteorder="big", signed=True)
            new_props["equalizer_preset"] = self.options.get(current_mode, f"unknown_{current_mode}")

        if current_mode in self.custom_preset_values:
            data = _eq_bytes_to_array(self.custom_preset_values[current_mode])
            new_props["equalizer_rows"] = json.dumps(data)

        await self.driver.put_property("sound", None, new_props,
                                       extend_group=True)


def _eq_bytes_to_array(data: bytes):
    return [int.from_bytes((x,), byteorder="big", signed=True) for x in data]


def _parse_custom_mode(data: bytes):
    count_lines = data[1]
    data_lines = data[2:2 + count_lines]
    label = data[2 + count_lines:].split(b"\x00", 1)[0].decode("utf8")
    return data[0], label, data_lines


def _build_payload(mode_id: int, mode_str: str, data: bytes, action: int):
    return [
        (1, mode_id),
        (2, len(data)),
        (3, data),
        (4, mode_str.encode("utf8")),
        (5, action),
    ]
