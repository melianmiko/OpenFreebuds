import json
from dataclasses import dataclass

from openfreebuds.driver.huawei.constants import CMD_FEATURES
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.exceptions import OfbNotSupportedError
from openfreebuds.utils import reverse_dict

HEAD_GESTURE_OPTIONS = {
    1: "tap_action_answer",
    2: "tap_action_reject",
    0: "tap_action_off",
}


@dataclass(frozen=True)
class _Field:
    group: str
    prop: str
    param: int
    options: dict[int, str] | None = None


@dataclass(frozen=True)
class _Feature:
    feature_id: int
    read_params: tuple[int, ...]
    fields: tuple[_Field, ...]


SPATIAL_AUDIO = _Feature(0x18, (2, 3), (
    _Field("sound", "spatial_audio", 2, {
        0: "spatial_off",
        2: "spatial_fixed",
        1: "spatial_head_tracking",
    }),
    _Field("sound", "spatial_audio_effect", 3, {
        0: "spatial_effect_default",
        1: "spatial_effect_theater",
        2: "spatial_effect_cinema",
        3: "spatial_effect_concert_hall",
    }),
))
HEAD_GESTURES = _Feature(0x0b, (), (
    _Field("action", "head_gestures", 2),
    _Field("action", "head_nod", 3, HEAD_GESTURE_OPTIONS),
    _Field("action", "head_shake", 4, HEAD_GESTURE_OPTIONS),
))
SINGLE_BUD_ANC = _Feature(0x05, (2,), (
    _Field("config", "single_bud_anc", 2),
))


class OfbHuaweiFeaturesHandler(OfbDriverHandlerHuawei):
    """
    Settings addressed by feature id through one command (2bb4).
    Param 1 is the feature id, other params are its fields.

    Tested on FreeBuds 7i
    """

    handler_id = "features"
    commands = [CMD_FEATURES]

    def __init__(self, w_spatial_audio=False, w_head_gestures=False, w_single_bud_anc=False):
        self.features: dict[int, _Feature] = {}
        for enabled, feature in [
            (w_spatial_audio, SPATIAL_AUDIO),
            (w_head_gestures, HEAD_GESTURES),
            (w_single_bud_anc, SINGLE_BUD_ANC),
        ]:
            if enabled:
                self.features[feature.feature_id] = feature

        self.fields: dict[tuple[str, str], tuple[_Feature, _Field]] = {}
        for feature in self.features.values():
            for field in feature.fields:
                self.fields[(field.group, field.prop)] = (feature, field)
        self.properties = list(self.fields.keys())

    async def on_init(self):
        for feature in self.features.values():
            resp = await self.driver.send_package(HuaweiSppPackage(CMD_FEATURES, resp=CMD_FEATURES, parameters=[
                (1, feature.feature_id),
                *[(p, b"") for p in feature.read_params],
            ]))
            await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        feature_id = package.find_param(1)
        if len(feature_id) != 1 or feature_id[0] not in self.features:
            return

        for field in self.features[feature_id[0]].fields:
            value = package.find_param(field.param)
            if len(value) != 1:
                continue
            if field.options is None:
                await self.driver.put_property(field.group, field.prop, json.dumps(value[0] == 1))
            else:
                await self.driver.put_property(field.group, None, {
                    field.prop: field.options.get(value[0], str(value[0])),
                    f"{field.prop}_options": ",".join(field.options.values()),
                }, extend_group=True)

    async def set_property(self, group: str, prop: str, value: str):
        if (group, prop) not in self.fields:
            raise OfbNotSupportedError(f"Unknown feature property {group}//{prop}")

        feature, field = self.fields[(group, prop)]
        if field.options is None:
            value_byte = 1 if value == "true" else 0
        else:
            value_byte = reverse_dict(field.options)[value]

        resp = await self.driver.send_package(HuaweiSppPackage.change_rq(CMD_FEATURES, [
            (1, feature.feature_id),
            (field.param, value_byte),
        ]))
        await self.on_package(resp)
