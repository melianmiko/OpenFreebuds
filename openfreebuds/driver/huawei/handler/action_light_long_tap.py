import asyncio
from dataclasses import dataclass

from openfreebuds.driver.huawei.constants import CMD_LIGHT_LONG_TAP_READ, CMD_LIGHT_LONG_TAP_WRITE
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


@dataclass(frozen=True)
class HuaweiLightTapSpec:
    prop_prefix: str
    gesture_type: int
    scene: int
    w_right: bool = True
    shared: bool = False
    options: dict[int, str] | None = None


class OfbHuaweiActionLightLongTapHandler(OfbDriverHandlerHuawei):
    """
    Newer pinch-and-hold gesture configuration handler.
    """

    handler_id = "gesture_light_long"
    commands = [CMD_LIGHT_LONG_TAP_READ, CMD_LIGHT_LONG_TAP_WRITE]
    init_timeout = 12
    init_attempt_max = 1

    def __init__(self, gesture_type: int = 3, scene: int = 0, w_right: bool = True,
                 options: dict[int, str] | None = None, specs: list[HuaweiLightTapSpec] | None = None):
        default_options = options or {
            -1: "tap_action_off",
            5: "tap_action_assistant",
            6: "tap_action_switch_anc",
        }
        self.specs = specs or [
            HuaweiLightTapSpec("light_long_tap", gesture_type, scene, w_right=w_right, options=default_options),
        ]
        self._options = {
            spec.prop_prefix: spec.options or default_options
            for spec in self.specs
        }
        self._supported_options = dict(self._options)

        self.properties = []
        for spec in self.specs:
            if spec.shared:
                self.properties.append(("action", spec.prop_prefix))
                continue

            self.properties.append(("action", f"{spec.prop_prefix}_left"))
            if spec.w_right:
                self.properties.append(("action", f"{spec.prop_prefix}_right"))

    async def on_init(self):
        for spec in self.specs:
            try:
                resp = await self.driver.send_package(
                    self._read_package(spec),
                    timeout=2,
                    response_matcher=lambda package, current_spec=spec: self._matches_spec_response(package, current_spec),
                )
            except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
                continue

            if resp is not None:
                await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None or package.is_error_response():
            return
        if package.command_id != CMD_LIGHT_LONG_TAP_READ:
            return

        spec = self._spec_from_package(package)
        if spec is None:
            return

        left = package.find_param(3)
        right = package.find_param(4)
        available_options = package.find_param(5)
        if len(available_options) > 0:
            self._supported_options[spec.prop_prefix] = self._options_from_supported_payload(spec, available_options)

        if spec.shared:
            value = left if len(left) == 1 else right
            if len(value) == 1:
                await self._put_action_value(spec, spec.prop_prefix, int.from_bytes(value, byteorder="big", signed=True))
            await self._put_options_value(spec)
            return

        if len(left) == 1:
            value = int.from_bytes(left, byteorder="big", signed=True)
            await self._put_action_value(spec, f"{spec.prop_prefix}_left", value)
        if len(right) == 1 and spec.w_right:
            value = int.from_bytes(right, byteorder="big", signed=True)
            await self._put_action_value(spec, f"{spec.prop_prefix}_right", value)

        await self._put_options_value(spec)

    async def set_property(self, group: str, prop: str, value):
        spec = self._spec_by_prop(prop)
        if spec is None:
            return

        if spec.shared:
            param_values = [(3, self._option_to_raw_value(spec, value)), (4, self._option_to_raw_value(spec, value))]
            confirm_params = (3, 4)
        elif prop == f"{spec.prop_prefix}_left":
            param_type = 3
            param_values = [(param_type, self._option_to_raw_value(spec, value))]
            confirm_params = (param_type,)
        elif prop == f"{spec.prop_prefix}_right":
            param_type = 4
            param_values = [(param_type, self._option_to_raw_value(spec, value))]
            confirm_params = (param_type,)
        else:
            return

        pkg = HuaweiSppPackage.change_rq(CMD_LIGHT_LONG_TAP_WRITE, [
            (1, spec.gesture_type),
            (2, spec.scene),
            *param_values,
        ])
        resp = await self.driver.send_package(
            pkg,
            response_matcher=lambda package: self._matches_spec_response(package, spec),
        )
        if resp is None or resp.is_error_response():
            return

        status = resp.find_param(5)
        if len(status) > 0 and status[0] != 0:
            return

        for confirm_param in confirm_params:
            confirmed_value = resp.find_param(confirm_param)
            if len(confirmed_value) == 1:
                await self._put_action_value(spec, prop, int.from_bytes(confirmed_value, byteorder="big", signed=True))
                return

        read_resp = await self.driver.send_package(
            self._read_package(spec),
            response_matcher=lambda package: self._matches_spec_response(package, spec),
        )
        if read_resp is not None:
            await self.on_package(read_resp)

    @staticmethod
    def _read_package(spec: HuaweiLightTapSpec):
        return HuaweiSppPackage(
            CMD_LIGHT_LONG_TAP_READ,
            [(1, spec.gesture_type), (2, spec.scene)],
            resp=CMD_LIGHT_LONG_TAP_READ,
        )

    def _options_from_supported_payload(self, spec: HuaweiLightTapSpec, payload: bytes) -> dict[int, str]:
        supported_values = []
        for raw_value in payload:
            value = int.from_bytes(bytes([raw_value]), byteorder="big", signed=True)
            supported_values.append(value)

        options = {
            value: label
            for value, label in self._options[spec.prop_prefix].items()
            if value in supported_values
        }
        for value in supported_values:
            if value not in options:
                options[value] = f"unknown_{value}"
        return options or self._options[spec.prop_prefix]

    async def _put_action_value(self, spec: HuaweiLightTapSpec, prop: str, value: int):
        supported_options = self._supported_options[spec.prop_prefix]
        fallback_options = self._options[spec.prop_prefix]
        await self.driver.put_property("action", prop, supported_options.get(value, fallback_options.get(value, f"unknown_{value}")))

    async def _put_options_value(self, spec: HuaweiLightTapSpec):
        await self.driver.put_property(
            "action",
            f"{spec.prop_prefix}_options",
            ",".join(self._supported_options[spec.prop_prefix].values()),
        )

    def _option_to_raw_value(self, spec: HuaweiLightTapSpec, value) -> int:
        for options in (self._supported_options[spec.prop_prefix], self._options[spec.prop_prefix]):
            reverse_options = reverse_dict(options)
            if value in reverse_options:
                return reverse_options[value]
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.startswith("unknown_"):
            return int(value.removeprefix("unknown_"))
        return int(value)

    def _spec_by_prop(self, prop: str) -> HuaweiLightTapSpec | None:
        for spec in self.specs:
            if spec.shared and prop == spec.prop_prefix:
                return spec
            if prop == f"{spec.prop_prefix}_left" or (spec.w_right and prop == f"{spec.prop_prefix}_right"):
                return spec
        return None

    def _spec_from_package(self, package: HuaweiSppPackage) -> HuaweiLightTapSpec | None:
        if len(self.specs) == 1:
            return self.specs[0]

        for spec in self.specs:
            if self._package_has_spec_params(package, spec):
                return spec
        return None

    @classmethod
    def _matches_spec_response(cls, package: HuaweiSppPackage, spec: HuaweiLightTapSpec) -> bool:
        if package.is_error_response():
            return True
        if package.command_id not in (CMD_LIGHT_LONG_TAP_READ, CMD_LIGHT_LONG_TAP_WRITE):
            return False
        return cls._package_has_spec_params(package, spec)

    @staticmethod
    def _package_has_spec_params(package: HuaweiSppPackage, spec: HuaweiLightTapSpec) -> bool:
        gesture_type = package.find_param(1)
        scene = package.find_param(2)
        if len(gesture_type) == 1 and gesture_type[0] != spec.gesture_type:
            return False
        if len(scene) == 1 and scene[0] != spec.scene:
            return False
        return True