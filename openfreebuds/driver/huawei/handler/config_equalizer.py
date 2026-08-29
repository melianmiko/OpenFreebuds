import json
from typing import Optional

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import OfbNotSupportedError, OfbTooManyItemsError
from openfreebuds.utils.logger import create_logger

KNOWN_BUILT_IN_PRESETS = {
    1: "equalizer_preset_default",
    2: "equalizer_preset_hardbass",
    3: "equalizer_preset_treble",
    9: "equalizer_preset_voices",
    10: "equalizer_preset_dynamic",
}
FAKE_BUILT_IN_PRESETS = [
    (-56, "equalizer_preset_symphony", "0f0f0afb0f190ffb322d"),
    (-55, "equalizer_preset_hi_fi_live", "fb141e0a0000e7f60a00"),
]
FAKE_BUILT_IN_PRESETS_COPY_NAME = {
    "equalizer_preset_symphony": "Symphony (copy)",
    "equalizer_preset_hi_fi_live": "Hi-Fi Live (Copy)",
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
        ("sound", "equalizer_saved"),
    ]
    commands = [b"\x2b\x4a"]
    ignore_commands = [b"\x2b\x49"]

    def __init__(
            self,
            w_presets: Optional[dict[int, str]] = None,
            w_custom: bool = False,
            w_fake_built_in: bool = False,
            wo_read: bool = False,
            w_custom_rows: int = 10,
            w_custom_max_count: int = 3,
    ):
        """
        Equalizer configuration handler

        @param w_presets: Available built-in presets
        @param w_custom: Allow custom modes flag
        @param w_fake_built_in: Allow fake built-in modes flag
        @param wo_read: Disallow read request flag (for legacy devices)
        @param w_custom_rows: Count of equalizer rows, for custom modes
        @param w_custom_max_count: Max count of custom modes available in device
        """
        self.w_custom: bool = w_custom
        self.wo_read: bool = wo_read
        self.w_custom_rows = w_custom_rows
        self.w_custom_max_count = w_custom_max_count
        self.w_fake_built_in = w_fake_built_in
        self.w_options_predefined: bool = w_presets is not None

        self.changes_saved: bool = True
        self.current_rollback_data: bytes = b""
        self.default_preset_data: list[tuple[Optional[int], str, Optional[str]]] = []
        self.data_overrides: dict[int, str] = {}

        # Predefined set of built-in modes
        if w_presets is not None:
            for i, name in w_presets.items():
                self.default_preset_data.append((i, f'equalizer_preset_{name}', None))

        # Load predefined presets
        if w_fake_built_in:
            self.default_preset_data.extend((a, b, None) for a, b, c in FAKE_BUILT_IN_PRESETS)
            self.data_overrides = {i: d for i, _, d in FAKE_BUILT_IN_PRESETS}
        elif w_custom:
            self.default_preset_data.extend((None, b, c) for _, b, c in FAKE_BUILT_IN_PRESETS)

        self.preset_data = self.default_preset_data

    async def on_init(self):
        if self.wo_read:
            await self.driver.put_property("sound", None, {
                "equalizer_preset": "",
                "equalizer_preset_options": ",".join([l for _, l, _ in self.preset_data])
            }, extend_group=True)
            return

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
        elif prop == "equalizer_saved":
            return await self._toggle_save(value == "true")

        raise OfbNotSupportedError("Impossible error")

    async def _toggle_save(self, save: bool):
        mode_id, mode_str, data = await self.find_current_mode()
        if mode_id is None:
            log.info(f"Skip unknown mode override {mode_str}")
            return

        if save:
            log.info(f"Will save persistent preset data={data}, mode_id={mode_id}")
        else:
            data = self.current_rollback_data
            log.info(f"Will restore saved data={data}, mode_id={mode_id}")

        pkg = HuaweiSppPackage.change_rq(
            b"\x2b\x49",
            _build_payload(mode_id, mode_str, data, 1)
        )
        await self.driver.send_package(pkg)
        await self.driver.put_property("sound", "equalizer_rows",
                                       json.dumps(_eq_bytes_to_array(data)))
        await self.driver.put_property("sound", "equalizer_saved", "true")
        self.changes_saved = True

    async def _change_current_mode(self, value: str):
        mode_id, mode_str, mode_data = await self.find_current_mode()
        if mode_id is None:
            log.info(f"Skip unknown mode override {mode_str}")
            return

        data = b"".join([x.to_bytes(1, byteorder="big", signed=True) for x in json.loads(value)])
        if self.changes_saved:
            self.current_rollback_data = mode_data
        log.info(f"Will replace id={mode_id}, label={mode_str} with data={data}")

        pkg = HuaweiSppPackage.change_rq(
            b"\x2b\x49",
            _build_payload(mode_id, mode_str, data, 1)
        )
        await self.driver.send_package(pkg)
        await self.driver.put_property("sound", "equalizer_rows", value)
        await self.driver.put_property("sound", "equalizer_saved", "false")
        self.changes_saved = False

    async def _delete_current_mode(self):
        mode_id, mode_str, mode_data = await self.find_current_mode()
        if mode_id is None:
            log.info(f"Skip unknown mode deletion {mode_str}")
            return

        log.info(f"Delete id={mode_id}, label={mode_str}, data={mode_data}")

        pkg = HuaweiSppPackage.change_rq(
            b"\x2b\x49",
            _build_payload(mode_id, mode_str, mode_data, 2)
        )
        await self.driver.send_package(pkg)
        await self.on_init()

    async def find_current_mode(self):
        mode_str = await self.driver.get_property("sound", "equalizer_preset", None)
        candidates = [(p_id, label, data) for p_id, label, data in self.preset_data if label == mode_str]
        if len(candidates) < 1:
            return None, None, None
        return candidates[0]

    async def _set_current_mode(self, mode_str):
        candidates = [(p_id, label, data) for p_id, label, data in self.preset_data if label == mode_str]
        custom_modes = [p_id for p_id, _, data in self.preset_data if data is not None and p_id is not None]
        mode_id = 0

        # What is going to do?
        if len(candidates) < 1:
            # Create new mode from scratch
            mode_data = b"\x00" * self.w_custom_rows
            current_mode = await self.driver.get_property("sound", "equalizer_preset", None)
            candidate_data = [data for _, label, data in self.preset_data if label == current_mode]
            if len(candidate_data) > 0 and candidate_data[0] is not None:
                mode_data = candidate_data[0]

            do_create = True
        elif candidates[0][0] is None:
            # Load predefined mode as custom
            mode_id, _, mode_data = candidates[0]
            mode_str = FAKE_BUILT_IN_PRESETS_COPY_NAME.get(mode_str, mode_str)
            do_create = True
        else:
            mode_id, mode_str_orig, mode_data = candidates[0]
            if mode_id in self.data_overrides:
                mode_data = self.data_overrides[mode_id]
            do_create = False

        # Preparation for new mode
        if do_create:
            if not self.w_custom:
                raise OfbNotSupportedError("Device didn't support custom equalizer presets")
            if len(custom_modes) >= self.w_custom_max_count:
                raise OfbTooManyItemsError()
            mode_id = 100
            while mode_id in custom_modes:
                mode_id += 1
            self.preset_data.append((mode_id, mode_str, mode_data))
            log.info(f"Will create new preset id={mode_id}, data={mode_data}")

        if mode_data is not None:
            # Is custom mode, use advanced payload
            pkg = HuaweiSppPackage.change_rq(
                b"\x2b\x49",
                _build_payload(mode_id, mode_str, mode_data, 1)
            )
        else:
            # Is built-in mode
            pkg = HuaweiSppPackage.change_rq(
                b"\x2b\x49",
                [(1, mode_id)]
            )

        self.changes_saved = True

        if self.wo_read:
            pkg.response_id = b""

        await self.driver.send_package(pkg)

        if self.wo_read:
            await self.driver.put_property("sound", "equalizer_preset", mode_str)
        else:
            await self.on_init()

    async def on_package(self, package: HuaweiSppPackage):
        new_props = {
            "equalizer_rows": None,
            "equalizer_saved": json.dumps(self.changes_saved),
            "equalizer_rows_count": str(self.w_custom_max_count),
            "equalizer_max_custom_modes": str(self.w_custom_max_count) if self.w_custom else "0"
        }

        available_modes = package.find_param(3)
        self.preset_data = []
        if not self.w_options_predefined and len(available_modes) > 0:
            for p_id in available_modes:
                self.preset_data.append((p_id, KNOWN_BUILT_IN_PRESETS.get(p_id, f"preset_{p_id}"), None))
        self.preset_data.extend(self.default_preset_data)

        custom_modes = package.find_param(8)
        if self.w_custom and len(custom_modes) > 0:
            offset = 0
            while offset < len(custom_modes):
                mode_id, mode_label, mode_data = _parse_custom_mode(custom_modes[offset:offset + 36])
                self.preset_data.append((mode_id, mode_label, mode_data))
                # log.info(f"Read custom mode id={mode_id}, label={mode_label}, data={mode_data}")
                offset += 36

        log.info(self.preset_data)

        new_props["equalizer_preset_options"] = ",".join([l for _, l, _ in self.preset_data])
        if self.w_custom and not self.w_fake_built_in:
            new_props["equalizer_preset_create_options"] = ",".join(l for _, l, _ in FAKE_BUILT_IN_PRESETS)

        current_mode = package.find_param(2)
        if len(current_mode) == 1:
            current_mode = int.from_bytes(current_mode, byteorder="big", signed=True)
            value = f"unknown_{current_mode}"
            for p_id, label, data in self.preset_data:
                if p_id == current_mode:
                    value = label
                    if data is not None:
                        new_props["equalizer_rows"] = json.dumps(_eq_bytes_to_array(data))
                    break
            new_props["equalizer_preset"] = value

        await self.driver.put_property("sound", None, new_props,
                                       extend_group=True)


def _eq_bytes_to_array(data: bytes | str):
    if isinstance(data, str):
        data = bytes.fromhex(data)
    return [int.from_bytes((x,), byteorder="big", signed=True) for x in data]


def _parse_custom_mode(data: bytes):
    count_lines = data[1]
    data_lines = data[2:2 + count_lines].hex()
    label = data[2 + count_lines:].split(b"\x00", 1)[0].decode("utf8")
    return data[0], label, data_lines


def _build_payload(mode_id: int, mode_str: str, data: bytes | str, action: int):
    if isinstance(data, str):
        data = bytes.fromhex(data)
    return [
        (1, mode_id),
        (2, len(data)),
        (3, data),
        (4, mode_str.encode("utf8")),
        (5, action),
    ]
