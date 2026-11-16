import asyncio
import json
from pathlib import Path

from openfreebuds.driver.huawei.constants import (
    CMD_BOX_TONE,
    CMD_BOX_TONE_INFO,
    CMD_MBB_FEATURE,
    MBB_FEATURE_BOX_TONE,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.driver.huawei.prompt_tone import build_tone_package
from openfreebuds.driver.huawei.prompt_tone_upload import (
    ToneUploadError,
    ToneUploadNotReady,
    upload_tone_proto2,
)
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiBoxToneHandler")

# 0x2BB1 response fields (measured 2026-11-13 on FreeClip 2): 2 = switch, 3 = supported
_TONE_PARAM_ENABLED = 2
_TONE_PARAM_SUPPORT = 3

# 0x2B25 response fields: 1 = left worn, 2 = right worn, 3 = left in case, 4 = right in case
_INFO_PARAM_LEFT_IN_BOX = 3
_INFO_PARAM_RIGHT_IN_BOX = 4

# 0x2BB4 feature 16 (BOX_TONE) full payload (12 bytes):
#   b0 = master switch, b1 = lid-open switch, b2 = lid-open volume (0-15)
#   b3..b8 = devId (reported by the device, the earbud MAC; preserve on write)
#   b9..b10 = big-endian toneId, b11 = select (0 = built-in fixed tone 'Unfold', 1 = uploaded audio)
# Single-byte writes have no effect; the full payload must be written to p2.
_F16_MASTER = 0
_F16_LID = 1
_F16_VOLUME = 2
_F16_DEVID = slice(3, 9)
_F16_TONE_ID = slice(9, 11)
_F16_SELECT = 11
_F16_PAYLOAD_LEN = 12
_VOLUME_MAX = 15

_MBB_READ_TIMEOUT = 0.5
_F16_WRITE_TIMEOUT = 1.0


def _build_tone_state_rq():
    """Build the 0x2BB1 query: 02 00 03 00"""
    return HuaweiSppPackage.read_rq(CMD_BOX_TONE, [_TONE_PARAM_ENABLED, _TONE_PARAM_SUPPORT])


def _build_tone_info_rq():
    """Build the 0x2B25 query: 01 00 02 00 03 00 04 00"""
    return HuaweiSppPackage.read_rq(CMD_BOX_TONE_INFO, [1, 2, 3, 4])


def _build_mbb_read_rq():
    """Build the 0x2BB4 BOX_TONE query: 01 01 10 02 00"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (1, MBB_FEATURE_BOX_TONE),
        (2, b""),
    ])


def _build_master_write_rq(enabled: bool):
    """Build the 0x2BB1 master-switch write: 01 01 <0/1>"""
    return HuaweiSppPackage.change_rq(CMD_BOX_TONE, [(1, 1 if enabled else 0)])


def _build_f16_write_rq(payload: bytes):
    """Build the 0x2BB4 BOX_TONE full write: 01 01 10 02 0c <payload>"""
    return HuaweiSppPackage.change_rq(CMD_MBB_FEATURE, [
        (1, MBB_FEATURE_BOX_TONE),
        (2, payload),
    ])


class OfbHuaweiBoxToneHandler(OfbDriverHandlerHuawei):
    """Charging-case tone handler (0x2BB1 master switch, 0x2B25 in-case state, 0x2BB4 feature 16 lid-open tone / tone id)."""

    handler_id = "config_box_tone"
    commands = [CMD_BOX_TONE, CMD_BOX_TONE_INFO, CMD_MBB_FEATURE]
    init_timeout = 3
    init_attempt_max = 3
    properties = [
        ("config", "box_tone_enabled"),
        ("config", "box_tone_supported"),
        ("config", "box_tone_lid_enabled"),
        ("config", "box_tone_lid_volume"),
        ("config", "box_tone_lid_supported"),
        ("config", "box_tone_id"),
        ("config", "box_tone_refresh"),
        ("config", "box_tone_device_id"),
        ("config", "box_tone_upload"),
        ("config", "box_tone_upload_status"),
        ("config", "box_tone_upload_progress"),
        ("state", "headset_in_box"),
    ]

    def __init__(self):
        # Cache the last full payload reported by the device; write by patching fields while preserving devId and other invariants
        self._f16_payload: bytes | None = None

    async def on_init(self):
        await self.driver.put_property("config", "box_tone_lid_supported", "false")

        resp = await self.driver.send_package(_build_tone_state_rq())
        if resp is not None:
            await self.on_package(resp)

        resp = await self.driver.send_package(_build_tone_info_rq())
        if resp is not None:
            await self.on_package(resp)

        await self._refresh_f16()

    async def _refresh_f16(self):
        """Read feature 16; silently skip when older firmware does not respond (keep lid_supported=false)."""
        try:
            resp = await self.driver.send_package(_build_mbb_read_rq(), timeout=_MBB_READ_TIMEOUT)
        except TimeoutError:
            log.info("No MBB box tone response, skipping lid tone controls")
            return
        if resp is not None:
            await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        if package is None:
            return

        if package.command_id == CMD_BOX_TONE:
            await self._on_tone_state(package)
        elif package.command_id == CMD_BOX_TONE_INFO:
            await self._on_tone_info(package)
        elif package.command_id == CMD_MBB_FEATURE:
            await self._on_mbb_feature(package)

    async def _on_tone_state(self, package: HuaweiSppPackage):
        new_props = {}

        enabled = package.find_param(_TONE_PARAM_ENABLED)
        if len(enabled) >= 1:
            new_props["box_tone_enabled"] = json.dumps(enabled[0] == 1)

        support = package.find_param(_TONE_PARAM_SUPPORT)
        if len(support) >= 1:
            new_props["box_tone_supported"] = json.dumps(support[0] == 1)

        if len(new_props) > 0:
            await self.driver.put_property("config", None, new_props, extend_group=True)

    async def _on_tone_info(self, package: HuaweiSppPackage):
        left = package.find_param(_INFO_PARAM_LEFT_IN_BOX)
        right = package.find_param(_INFO_PARAM_RIGHT_IN_BOX)
        if len(left) == 0 and len(right) == 0:
            return

        left_in_box = len(left) == 1 and left[0] == 1
        right_in_box = len(right) == 1 and right[0] == 1
        # Only both earbuds in the case counts as in_box; one earbud in the case cannot change the tone
        is_in_box = left_in_box and right_in_box

        await self.driver.put_property("state", "headset_in_box", json.dumps(is_in_box))

    async def _on_mbb_feature(self, package: HuaweiSppPackage):
        feature = package.find_param(1)
        if len(feature) == 0 or feature[0] != MBB_FEATURE_BOX_TONE:
            return

        payload = package.find_param(2)
        if len(payload) < _F16_PAYLOAD_LEN:
            # Payload shorter than 12 bytes -> lid-open tone not supported
            await self.driver.put_property("config", "box_tone_lid_supported", "false")
            return

        self._f16_payload = bytes(payload)
        new_props = {
            "box_tone_lid_supported": "true",
            "box_tone_enabled": json.dumps(payload[_F16_MASTER] != 0),
            "box_tone_lid_enabled": json.dumps(payload[_F16_LID] != 0),
            "box_tone_lid_volume": str(payload[_F16_VOLUME]),
            "box_tone_id": str(int.from_bytes(payload[_F16_TONE_ID], "big")),
            "box_tone_device_id": payload[_F16_DEVID].hex(),
        }
        await self.driver.put_property("config", None, new_props, extend_group=True)

    async def _refresh_in_box_state(self) -> bool:
        """Before acting, request 0x2B25 once and then read state so a stale value cannot let the write through."""
        try:
            resp = await self.driver.send_package(_build_tone_info_rq())
        except TimeoutError:
            log.warning("In-box refresh timed out before box tone write")
            return False
        except Exception:
            log.exception("In-box refresh failed before box tone write")
            return False
        if resp is not None:
            await self.on_package(resp)
        return await self.driver.get_property("state", "headset_in_box") == "true"

    async def set_property(self, group: str, prop: str, value: str):
        if prop == "box_tone_refresh":
            # GUI triggers this when both earbuds just entered the case: re-read feature 16 (current tone id / lid-open settings)
            await self._refresh_f16()
            return True

        if prop == "box_tone_upload":
            return await self._upload_tone(value)

        if prop not in ("box_tone_enabled", "box_tone_lid_enabled",
                        "box_tone_lid_volume", "box_tone_id"):
            log.warning(f"Property {group}//{prop} is read-only, ignoring write")
            return False

        # Dragging back to the original value is not a device write, so no in-case refresh is needed
        if prop == "box_tone_lid_volume":
            if await self.driver.get_property("config", "box_tone_lid_volume") == value:
                return True

        if not await self._refresh_in_box_state():
            log.warning(f"Headset isn't fully in the charging case, ignoring write {group}//{prop}")
            return False

        if prop == "box_tone_enabled":
            return await self._write_master(value == "true")

        if self._f16_payload is None:
            log.warning("Device doesn't support lid tone, ignoring write")
            return False

        if prop == "box_tone_id":
            return await self._write_tone_id(value)
        if prop == "box_tone_lid_enabled":
            return await self._write_lid_enabled(value == "true")
        return await self._write_lid_volume(value)

    async def _write_master(self, enabled: bool):
        if await self.driver.get_property("config", "box_tone_supported") == "false":
            log.warning("Device doesn't support box tone, ignoring write")
            return False

        try:
            resp = await self.driver.send_package(_build_master_write_rq(enabled))
        except TimeoutError:
            resp = None
        if resp is not None:
            await self.on_package(resp)
        return True

    async def _send_f16(self, payload: bytes):
        """Write the full feature 16 payload. FreeClip 2 does not always ACK; do not surface a timeout to the UI, re-read and trust the device value, and keep the local value if readback also fails."""
        try:
            resp = await self.driver.send_package(
                _build_f16_write_rq(payload), timeout=_F16_WRITE_TIMEOUT)
        except TimeoutError:
            resp = None
        if resp is not None:
            await self.on_package(resp)
        else:
            await self._refresh_f16()

    async def _write_lid_enabled(self, enabled: bool):
        payload = bytearray(self._f16_payload)
        # b0 follows the current master switch so a full write does not restore an old master state
        master_on = await self.driver.get_property("config", "box_tone_enabled") == "true"
        payload[_F16_MASTER] = 1 if master_on else 0
        payload[_F16_LID] = 1 if enabled else 0
        await self._send_f16(bytes(payload))
        return True

    async def _write_lid_volume(self, value: str):
        try:
            volume = int(value)
        except (TypeError, ValueError):
            log.warning(f"Invalid lid tone volume {value}, ignoring write")
            return False
        if not 0 <= volume <= _VOLUME_MAX:
            log.warning(f"Lid tone volume {volume} is out of range, ignoring write")
            return False

        if volume == self._f16_payload[_F16_VOLUME]:
            # Dragging to the original value must not disturb the earbuds
            return True

        payload = bytearray(self._f16_payload)
        payload[_F16_VOLUME] = volume
        await self._send_f16(bytes(payload))
        return True

    async def _write_tone_id(self, value: str):
        try:
            tone_id = int(value)
        except (TypeError, ValueError):
            log.warning(f"Invalid tone id {value}, ignoring write")
            return False
        if not 0 <= tone_id <= 0xFFFF:
            log.warning(f"Tone id {tone_id} is out of range, ignoring write")
            return False

        payload = bytearray(self._f16_payload)
        payload[_F16_TONE_ID] = tone_id.to_bytes(2, "big")
        # select: 0 = built-in fixed tone (only id 0 'Unfold'), 1 = uploaded audio on the earbuds
        payload[_F16_SELECT] = 0 if tone_id == 0 else 1
        await self._send_f16(bytes(payload))
        # id 0 is the earbuds' own tone and needs no audio upload; give the UI a displayable completion state.
        # Other ids only change slots; clear the stale 'audio not uploaded' state.
        await self.driver.put_property(
            "config", "box_tone_upload_status", "builtin" if tone_id == 0 else "")
        return True

    async def _set_status(self, status: str):
        """Upload status uses stable state codes; the UI translates them (no localized text is assembled here)."""
        await self.driver.put_property("config", "box_tone_upload_status", status)

    async def _set_progress(self, percent: int):
        await self.driver.put_property("config", "box_tone_upload_progress", str(percent))

    async def _upload_tone(self, value: str):
        """Upload an existing PCM into an earbud slot: write feature16 toneId first, then stream the full package, matching the official App order (id first, then package).
        Input JSON: {"id": 151, "path": "...pcm", "name": "huawei_intelligence_ai1"}
        """
        try:
            request = json.loads(value)
            tone_id = int(request["id"])
            path = Path(request["path"])
            name = str(request.get("name") or "tone")
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            log.warning(f"Invalid tone upload request: {value}")
            return False

        if self._f16_payload is None:
            await self._set_status("unsupported")
            return False

        # Id 0 is a real built-in tone: write feature16 only (toneId=0, select=0) and never stream audio
        if tone_id == 0:
            await self._write_tone_id("0")
            return True

        if not path.is_file():
            await self._set_status("file_missing")
            return False

        if not await self._refresh_in_box_state():
            log.warning("Tone upload ignored: earbuds aren't both in the charging case")
            return False

        try:
            pcm = path.read_bytes()
            package = build_tone_package(pcm, name.encode("ascii", "ignore").decode("ascii") or "tone")
        except (OSError, ValueError) as e:
            log.warning(f"Can't prepare tone package: {e}")
            await self._set_status("failed")
            return False

        # A slot must be selected first, otherwise the device does not know where to store the audio.
        # Note: _write_tone_id() clears upload_status, so set the state afterwards,
        # otherwise the progress bar disappears as soon as it appears.
        await self._write_tone_id(str(tone_id))

        await self._set_progress(0)
        await self._set_status("uploading")

        def _progress(percent: int):
            asyncio.create_task(self._set_progress(percent))

        try:
            async with self.driver.raw_session_all() as session:
                await upload_tone_proto2(session, package, progress_cb=_progress)
        except ToneUploadNotReady:
            log.warning("Device rejected tone upload (not ready)")
            await self._set_status("device_rejected")
            return False
        except ToneUploadError as e:
            log.warning(f"Tone upload failed: {e}")
            await self._set_status("upload_failed")
            return False
        except Exception:
            log.exception("Tone upload crashed")
            await self._set_status("upload_failed")
            return False

        await self._set_progress(100)
        await self._set_status("done")
        return True
