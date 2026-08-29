import asyncio
import json
from dataclasses import dataclass

from openfreebuds.driver.huawei.constants import CMD_FEATURE_SWITCH
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import OfbNotSupportedError


@dataclass(frozen=True)
class HuaweiFeatureSwitchSpec:
    feature_id: int
    write_payload_size: int = 1
    state_param: int = 2
    group: str | None = None
    read_params: tuple[int, ...] | None = None
    truthy_values: tuple[int, ...] = (1,)
    options: dict[int, str] | None = None
    value_type: str = "bool"


class OfbHuaweiFeatureSwitchHandler(OfbDriverHandlerHuawei):
    """
    Newer Huawei feature switch handler.

    The official Huawei Audio Connect app uses command 2bb4 for a set of
    feature toggles. Each request carries feature id in param 1 and state in
    param 2: empty state for read, 0/1 for write.
    """

    handler_id = "feature_switch"
    commands = [CMD_FEATURE_SWITCH]

    init_timeout = 12
    init_attempt_max = 1

    def __init__(self, features: dict[str, int | HuaweiFeatureSwitchSpec], group: str = "features"):
        self.feature_specs = {prop: self._coerce_spec(spec) for prop, spec in features.items()}
        self.features = {prop: spec.feature_id for prop, spec in self.feature_specs.items()}
        self.group = group
        self.feature_by_id: dict[int, list[str]] = {}
        for prop, feature_id in self.features.items():
            self.feature_by_id.setdefault(feature_id, []).append(prop)
        self.properties = [(self._group_for_spec(spec), prop) for prop, spec in self.feature_specs.items()]

    async def on_init(self):
        seen_requests = set()
        for spec in self.feature_specs.values():
            request = self._read_request(spec)
            request_key = request.to_bytes()
            if request_key in seen_requests:
                continue
            seen_requests.add(request_key)

            try:
                resp = await self._send_for_spec(request, spec, timeout=2)
            except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
                continue

            if resp is not None:
                await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
        if prop not in self.features:
            raise OfbNotSupportedError("Impossible error")

        spec = self.feature_specs[prop]
        if group != self._group_for_spec(spec):
            raise OfbNotSupportedError("Impossible error")

        state_value = self._value_to_int(spec, value)
        pkg = HuaweiSppPackage.change_rq(CMD_FEATURE_SWITCH, [
            (1, spec.feature_id),
            (spec.state_param, self._state_payload(spec, state_value)),
        ])
        resp = await self._send_for_spec(pkg, spec, timeout=3)
        if resp is None or resp.is_error_response():
            return

        await self.on_package(resp)

    async def _send_for_spec(self, pkg: HuaweiSppPackage, spec: HuaweiFeatureSwitchSpec, timeout: int):
        return await self.driver.send_package(
            pkg,
            timeout=timeout,
            response_matcher=lambda response: self._matches_feature_response(response, spec.feature_id),
        )

    async def on_package(self, package: HuaweiSppPackage):
        if package.is_error_response():
            return set()

        feature_id = package.find_param(1)
        if len(feature_id) != 1:
            return set()

        props = self.feature_by_id.get(feature_id[0])
        if props is None:
            return set()

        updated = set()
        for prop in props:
            spec = self.feature_specs[prop]
            state = package.find_param(spec.state_param)
            if len(state) < 1 and spec.state_param != 2:
                state = package.find_param(2)
            if len(state) < 1:
                continue

            await self.driver.put_property(self._group_for_spec(spec), prop, self._value_to_store(spec, state[0]))
            updated.add(prop)

        return updated

    @classmethod
    def _read_request(cls, spec: HuaweiFeatureSwitchSpec):
        read_params = spec.read_params if spec.read_params is not None else (2,)
        return HuaweiSppPackage(
            cmd=CMD_FEATURE_SWITCH,
            resp=CMD_FEATURE_SWITCH,
            parameters=[
                (1, spec.feature_id),
                *[(param, b"") for param in read_params],
            ],
        )

    @staticmethod
    def _state_payload(spec: HuaweiFeatureSwitchSpec, state_value: int) -> bytes:
        return bytes([state_value & 0xff]) + (b"\x00" * (spec.write_payload_size - 1))

    def _group_for_spec(self, spec: HuaweiFeatureSwitchSpec) -> str:
        return spec.group or self.group

    @staticmethod
    def _value_to_store(spec: HuaweiFeatureSwitchSpec, value: int) -> str:
        if spec.options is not None:
            return spec.options.get(value, f"unknown_{value}")
        if spec.value_type == "int":
            return str(value)
        return json.dumps(value in spec.truthy_values)

    @staticmethod
    def _value_to_int(spec: HuaweiFeatureSwitchSpec, value) -> int:
        if spec.options is not None:
            if isinstance(value, int):
                return value
            for raw_value, option_name in spec.options.items():
                if value == option_name:
                    return raw_value
            if isinstance(value, str) and value.startswith("unknown_"):
                return int(value.removeprefix("unknown_"))
            return int(value)
        if spec.value_type == "int":
            return int(value)
        return 1 if value == "true" or value is True else 0

    @staticmethod
    def _coerce_spec(spec: int | HuaweiFeatureSwitchSpec) -> HuaweiFeatureSwitchSpec:
        if isinstance(spec, HuaweiFeatureSwitchSpec):
            return spec
        return HuaweiFeatureSwitchSpec(spec)

    @staticmethod
    def _matches_feature_response(package: HuaweiSppPackage, feature_id: int) -> bool:
        if package.is_error_response():
            return True
        response_feature_id = package.find_param(1)
        return len(response_feature_id) == 1 and response_feature_id[0] == feature_id