import json

from openfreebuds.driver.huawei.constants import CMD_MBB_FEATURE, MBB_FEATURE_SPATIAL_AUDIO
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiSpatialAudioHandler")

# 0x2BB4 is the generic MBB path; spatial audio uses featureId 24 (0x18)
SPATIAL_AUDIO_FEATURE_ID = MBB_FEATURE_SPATIAL_AUDIO

# 0x2BB4 payload fields (measured 2026-11-13 across nine FreeClip 2 states):
#   1 = featureId (echoes 0x18)
#   2 = spatial mode (0 off, 1 head tracking, 2 fixed)
#   3 = spatial sound field (0 default, 1 theater, 2 cinema, 3 concert hall; kept when off)
_PARAM_FEATURE = 1
_PARAM_MODE = 2
_PARAM_ROOM = 3

MODE_OFF = 0
MODE_HEAD_TRACKING = 1
MODE_FIXED = 2

MODE_NAMES = {
    MODE_OFF: "off",
    MODE_HEAD_TRACKING: "head_tracking",
    MODE_FIXED: "fixed",
}
MODE_VALUES = {name: value for value, name in MODE_NAMES.items()}

ROOM_NAMES = {
    0: "default",
    1: "theater",
    2: "cinema",
    3: "concert_hall",
}
ROOM_VALUES = {name: value for value, name in ROOM_NAMES.items()}


def _build_read_rq():
    """Build the 0x2BB4 read request: 01 01 18 02 00 03 00"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, SPATIAL_AUDIO_FEATURE_ID),
        (_PARAM_MODE, b""),
        (_PARAM_ROOM, b""),
    ])


def _build_mode_rq(mode: int):
    """Build the 0x2BB4 mode write: 01 01 18 02 01 <0/1/2>"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, SPATIAL_AUDIO_FEATURE_ID),
        (_PARAM_MODE, mode),
    ])


def _build_room_rq(room: int):
    """Build the 0x2BB4 sound-field write: 01 01 18 03 01 <0..3>"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (_PARAM_FEATURE, SPATIAL_AUDIO_FEATURE_ID),
        (_PARAM_ROOM, room),
    ])


class OfbHuaweiSpatialAudioHandler(OfbDriverHandlerHuawei):
    """Independent (earbud-side) spatial audio handler (0x2BB4 MBB).

    Only FreeBuds 7 / 7i / Neo, FreeBuds Pro 5 and FreeClip 2 / 2 S are on
    Huawei's independent spatial audio list. Models whose ``spatialAudio``
    widget is Huawei-phone-side HD spatial audio, or fixed-only spatial audio,
    do not answer the switch query; do not mount this handler for them.
    """

    handler_id = "config_spatial_audio"
    commands = [CMD_MBB_FEATURE]
    init_timeout = 3
    init_attempt_max = 2
    properties = [
        ("sound", "spatial_audio"),
        ("sound", "spatial_audio_mode"),
        ("sound", "spatial_audio_room"),
        ("sound", "spatial_audio_supported"),
    ]

    def __init__(self):
        self.supported: bool = False
        self.current_mode: int = MODE_OFF
        self.current_room: int = 1

    async def on_init(self):
        try:
            resp = await self.driver.send_package(_build_read_rq(), timeout=2)
        except TimeoutError:
            resp = None
        if resp is None:
            await self.driver.put_property("sound", "spatial_audio_supported", "false")
            return

        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None or package.command_id != CMD_MBB_FEATURE:
            return

        # 0x2BB4 is the generic MBB path; when a feature section is present, handle only the spatial audio feature
        feature = package.find_param(_PARAM_FEATURE)
        if len(feature) == 0 or feature[0] != SPATIAL_AUDIO_FEATURE_ID:
            return

        self.supported = True
        new_props = {
            "spatial_audio_supported": "true",
        }

        room = package.find_param(_PARAM_ROOM)
        if len(room) == 1 and room[0] in ROOM_NAMES:
            self.current_room = room[0]
            new_props["spatial_audio_room"] = ROOM_NAMES[room[0]]

        mode = package.find_param(_PARAM_MODE)
        if len(mode) == 1 and mode[0] in MODE_NAMES:
            self.current_mode = mode[0]
            new_props["spatial_audio_mode"] = MODE_NAMES[mode[0]]
            new_props["spatial_audio"] = json.dumps(mode[0] != MODE_OFF)

        if len(new_props) > 0:
            await self.driver.put_property("sound", None, new_props, extend_group=True)

    async def set_property(self, group: str, prop: str, value: str):
        if not self.supported:
            log.warning(f"Device doesn't support spatial audio, ignoring write {group}//{prop}")
            return False

        if prop == "spatial_audio":
            enabled = value == "true"
            if enabled and self.current_mode == MODE_OFF:
                mode = MODE_HEAD_TRACKING
            elif not enabled:
                mode = MODE_OFF
            else:
                mode = self.current_mode
            return await self._send(_build_mode_rq(mode))

        if prop == "spatial_audio_mode":
            if value not in MODE_VALUES:
                log.warning(f"Unknown spatial audio mode {value}, ignoring write")
                return False
            return await self._send(_build_mode_rq(MODE_VALUES[value]))

        if prop == "spatial_audio_room":
            if value not in ROOM_VALUES:
                log.warning(f"Unknown spatial audio room {value}, ignoring write")
                return False
            return await self._send(_build_room_rq(ROOM_VALUES[value]))

        log.warning(f"Property {group}//{prop} is read-only, ignoring write")
        return False

    async def _send(self, package: HuaweiSppPackage) -> bool:
        resp = await self.driver.send_package(package)
        if resp is not None:
            await self.on_package(resp)
        return True
