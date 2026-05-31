import asyncio
import hashlib
import json
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

from openfreebuds.constants import STORAGE_PATH
from openfreebuds.driver.huawei.constants import (
    CMD_FEATURE_ABILITY,
    CMD_FEATURE_SWITCH,
    CMD_PROMPT_TONE_OTA_DATA,
    CMD_PROMPT_TONE_OTA_ERROR,
    CMD_PROMPT_TONE_OTA_OFFSET,
    CMD_PROMPT_TONE_OTA_PREPARE,
    CMD_PROMPT_TONE_OTA_PROGRESS,
    CMD_PROMPT_TONE_OTA_READY,
    CMD_PROMPT_TONE_OTA_START,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.driver.huawei.utils import crc16_xmodem
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiPromptToneHandler")

BOX_TONE_FEATURE_ID = 16
PROMPT_TONE_SUCCESS = 100000
PROMPT_TONE_CDN_ROOT = (
    "https://contentcenter-drru.dbankcdn.ru/pub_1/"
    "HW-SmartHome_oem_900_9/43/v3/ru/device/guide/00000A"
)
PROMPT_TONE_CONFIG_URL = f"{PROMPT_TONE_CDN_ROOT}/00000A_promptToneConfig.zip"
PROMPT_TONE_ARCHIVE_URL = f"{PROMPT_TONE_CDN_ROOT}/00000A_promptTone.zip"
PROMPT_TONE_OTA_HEADSET_BOXES_LOW_BATTERY = 109002
PROMPT_TONE_OTA_HEADSET_OTA_STATE = 109006
PROMPT_TONE_OTA_HEADSET_OUT_BOX = 109012
PROMPT_TONE_OTA_HEADSET_RECORDING = 109022
PROMPT_TONE_OTA_HEADSET_BOXES_LOW_BATTERY_LEVEL = 109024

PROMPT_TONE_ERROR_MESSAGES = {
    PROMPT_TONE_OTA_HEADSET_BOXES_LOW_BATTERY: "Charging case battery is too low",
    PROMPT_TONE_OTA_HEADSET_OTA_STATE: "Earbuds are busy with firmware update",
    PROMPT_TONE_OTA_HEADSET_OUT_BOX: "Put both earbuds into the charging case before changing case sounds",
    PROMPT_TONE_OTA_HEADSET_RECORDING: "Earbuds are busy with recording",
    PROMPT_TONE_OTA_HEADSET_BOXES_LOW_BATTERY_LEVEL: "Charging case battery is too low",
}


class PromptToneTransferError(RuntimeError):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class HuaweiPromptTone:
    tone_id: int
    name: str

    @property
    def file_name(self) -> str:
        return f"{self.name}.pcm"


PROMPT_TONES = [
    HuaweiPromptTone(0, "Unfold"),
    HuaweiPromptTone(43, "Whistle"),
    HuaweiPromptTone(4, "Bongo"),
    HuaweiPromptTone(7, "Chess"),
    HuaweiPromptTone(10, "Dewdrop"),
    HuaweiPromptTone(11, "Doorbell"),
    HuaweiPromptTone(12, "Drip"),
    HuaweiPromptTone(15, "Fountain"),
    HuaweiPromptTone(18, "Huawei_Cascade"),
    HuaweiPromptTone(22, "Leap"),
    HuaweiPromptTone(25, "Lit"),
    HuaweiPromptTone(26, "Little_Wish"),
    HuaweiPromptTone(28, "Meditation"),
    HuaweiPromptTone(31, "Pixies"),
    HuaweiPromptTone(32, "Play"),
    HuaweiPromptTone(34, "Pursue"),
    HuaweiPromptTone(35, "Rise"),
    HuaweiPromptTone(36, "Shine"),
]
PROMPT_TONE_BY_ID = {tone.tone_id: tone for tone in PROMPT_TONES}


@dataclass
class HuaweiPromptToneState:
    supported: bool = False
    protocol: int = 0
    state: int = 0
    enabled: bool = False
    volume: int = 0
    tone_device_id: str = "000000000000"
    tone_id: int = 0
    select: int = 0


class HuaweiPromptToneResourceCache:
    def __init__(self, root: Path | None = None):
        self.root = root or STORAGE_PATH / "huawei_prompt_tones" / "00000A"
        self.config_zip_path = self.root / "00000A_promptToneConfig.zip"
        self.archive_zip_path = self.root / "00000A_promptTone.zip"
        self.config_path = self.root / "tone_config.json"
        self.pcm_root = self.root / "pcm"

    def prepare(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.pcm_root.mkdir(parents=True, exist_ok=True)
        self._ensure_zip(PROMPT_TONE_CONFIG_URL, self.config_zip_path)
        self._ensure_zip(PROMPT_TONE_ARCHIVE_URL, self.archive_zip_path)
        self._extract_config()
        self._extract_pcm_files()

    def ensure_pcm(self, tone: HuaweiPromptTone) -> Path:
        path = self.pcm_root / tone.file_name
        if not path.is_file():
            self.prepare()
        if not path.is_file():
            raise FileNotFoundError(f"Prompt tone PCM not found in Huawei resource cache: {tone.file_name}")
        return path

    def _ensure_zip(self, url: str, path: Path):
        if path.is_file() and path.stat().st_size > 0:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with urlopen(url, timeout=60) as response, open(tmp_path, "wb") as file:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file.write(chunk)
        tmp_path.replace(path)

    def _extract_config(self):
        if self.config_path.is_file():
            return
        with zipfile.ZipFile(self.config_zip_path) as archive:
            entry = next(name for name in archive.namelist() if name.endswith("tone_config.json"))
            self.config_path.write_bytes(archive.read(entry))

    def _extract_pcm_files(self):
        missing = [tone for tone in PROMPT_TONES if not (self.pcm_root / tone.file_name).is_file()]
        if not missing:
            return
        with zipfile.ZipFile(self.archive_zip_path) as archive:
            for entry in archive.namelist():
                if not entry.lower().endswith(".pcm"):
                    continue
                target = self.pcm_root / Path(entry).name
                if not target.is_file():
                    target.write_bytes(archive.read(entry))


class OfbHuaweiPromptToneHandler(OfbDriverHandlerHuawei):
    handler_id = "prompt_tone"
    commands = [
        CMD_FEATURE_ABILITY,
        CMD_FEATURE_SWITCH,
        CMD_PROMPT_TONE_OTA_OFFSET,
        CMD_PROMPT_TONE_OTA_PROGRESS,
        CMD_PROMPT_TONE_OTA_ERROR,
    ]
    properties = [
        ("case_sound", "enabled"),
        ("case_sound", "volume"),
        ("case_sound", "tone_id"),
        ("case_sound", "prepare"),
    ]

    init_timeout = 8
    init_attempt_max = 1

    def __init__(
            self,
            cache: HuaweiPromptToneResourceCache | None = None,
            device_id_provider=None,
            transfer_settle_delay: float = 1.5,
            ota_write_delay: float = 0.012,
    ):
        self.cache = cache or HuaweiPromptToneResourceCache()
        self._device_id_provider = device_id_provider or _local_tone_device_id
        self._transfer_settle_delay = transfer_settle_delay
        self._ota_write_delay = max(0.0, ota_write_delay)
        self._state = HuaweiPromptToneState()
        self._ota_queue: asyncio.Queue[HuaweiSppPackage] | None = None
        self._transfer_lock = asyncio.Lock()

    async def on_init(self):
        await self._publish_static_properties()
        await self._query_ability()
        if self._state.supported:
            await self._read_state()

    async def on_package(self, package: HuaweiSppPackage):
        if self._ota_queue is not None and package.command_id in (
                CMD_PROMPT_TONE_OTA_OFFSET,
                CMD_PROMPT_TONE_OTA_PROGRESS,
                CMD_PROMPT_TONE_OTA_ERROR,
        ):
            await self._ota_queue.put(package)
            return

        if package.is_error_response():
            return
        if package.command_id == CMD_FEATURE_ABILITY:
            await self._parse_ability(package)
            return
        if package.command_id == CMD_FEATURE_SWITCH:
            await self._parse_state(package)
            return

    async def set_property(self, group: str, prop: str, value):
        if prop == "prepare":
            await self._prepare_resources()
            return
        if not self._state.supported:
            return

        if prop == "enabled":
            await self._write_state(enabled=value is True or value == "true")
        elif prop == "volume":
            await self._write_state(volume=max(0, min(15, int(value))))
        elif prop == "tone_id":
            tone_id = int(value)
            if tone_id == 0:
                await self._write_state(tone_id=0, tone_device_id=self._device_id_provider(), select=0)
            else:
                await self._transfer_tone(tone_id)

    async def _publish_static_properties(self):
        await self.driver.put_property(
            "case_sound",
            None,
            {
                "tone_options": ",".join(str(tone.tone_id) for tone in PROMPT_TONES),
                "tone_names": json.dumps({str(tone.tone_id): tone.name for tone in PROMPT_TONES}),
                "transfer_status": "idle",
                "transfer_progress": "0",
                "transfer_error": "",
                "storage_free": "unknown",
                "storage_total": "unknown",
                "storage_note": "Headset does not expose a separate prompt-tone free-space query; 0901/0902 reserve the transfer and 0907 reports refusal reasons.",
            },
            extend_group=True,
        )

    async def _prepare_resources(self):
        await self.driver.put_property(
            "case_sound",
            None,
            {"transfer_status": "downloading", "transfer_error": ""},
            extend_group=True,
        )
        await asyncio.to_thread(self.cache.prepare)
        await self.driver.put_property("case_sound", "transfer_progress", "0")
        await self.driver.put_property("case_sound", "transfer_status", "ready")

    async def _query_ability(self):
        pkg = HuaweiSppPackage(
            CMD_FEATURE_ABILITY,
            [(1, b"\x01"), (14, b""), (21, b"")],
            resp=CMD_FEATURE_ABILITY,
        )
        try:
            resp = await self.driver.send_package(pkg, timeout=3)
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            return
        if resp is not None:
            await self._parse_ability(resp)

    async def _parse_ability(self, package: HuaweiSppPackage):
        ota_payload = package.find_param(21)
        legacy_payload = package.find_param(14)

        if len(ota_payload) >= 2 and ota_payload[0] == 1 and ota_payload[1] == 1:
            self._state.supported = True
            self._state.protocol = 2
        elif len(legacy_payload) >= 2 and legacy_payload[0] == 1 and legacy_payload[1] == 1:
            self._state.supported = True
            self._state.protocol = 1
        else:
            return

        await self.driver.put_property(
            "case_sound",
            None,
            {
                "available": "true",
                "protocol": str(self._state.protocol),
            },
            extend_group=True,
        )

    async def _read_state(self):
        pkg = HuaweiSppPackage(CMD_FEATURE_SWITCH, [(1, BOX_TONE_FEATURE_ID)], resp=CMD_FEATURE_SWITCH)
        try:
            resp = await self.driver.send_package(
                pkg,
                timeout=3,
                response_matcher=lambda response: self._matches_box_tone(response),
            )
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            return
        if resp is not None:
            await self._parse_state(resp)

    async def _parse_state(self, package: HuaweiSppPackage):
        if not self._matches_box_tone(package):
            return
        payload = package.find_param(2)
        if len(payload) != 12:
            return

        self._state.state = payload[0]
        self._state.enabled = payload[1] == 1
        self._state.volume = payload[2]
        self._state.tone_device_id = payload[3:9].hex().upper()
        self._state.tone_id = int.from_bytes(payload[9:11], byteorder="big")
        self._state.select = payload[11]

        await self.driver.put_property(
            "case_sound",
            None,
            {
                "available": "true",
                "supported": json.dumps(self._state.state == 1),
                "enabled": json.dumps(self._state.enabled),
                "volume": str(self._state.volume),
                "tone_device_id": self._state.tone_device_id,
                "tone_id": str(self._state.tone_id),
                "tone_select": str(self._state.select),
            },
            extend_group=True,
        )

    async def _write_state(
            self,
            enabled: bool | None = None,
            volume: int | None = None,
            tone_id: int | None = None,
            tone_device_id: str | None = None,
            select: int | None = None,
    ):
        enabled = self._state.enabled if enabled is None else enabled
        volume = self._state.volume if volume is None else volume
        tone_id = self._state.tone_id if tone_id is None else tone_id
        tone_device_id = self._state.tone_device_id if tone_device_id is None else tone_device_id
        select = self._state.select if select is None else select

        payload = bytes([1, 1 if enabled else 0, volume & 0xff])
        payload += bytes.fromhex(f"{tone_device_id}{tone_id & 0xffff:04X}")
        payload += bytes([select & 0xff])

        pkg = HuaweiSppPackage.change_rq(CMD_FEATURE_SWITCH, [(1, BOX_TONE_FEATURE_ID), (2, payload)])
        try:
            resp = await self.driver.send_package(
                pkg,
                timeout=4,
                response_matcher=lambda response: self._matches_box_tone(response),
            )
        except (TimeoutError, ConnectionResetError, asyncio.TimeoutError):
            await self._read_state()
            return
        if resp is not None and not resp.is_error_response():
            await self._parse_state(resp)

    async def _transfer_tone(self, tone_id: int):
        async with self._transfer_lock:
            if self._state.protocol != 2:
                log.warning("Prompt tone protocol %s is not implemented", self._state.protocol)
                return
            tone = PROMPT_TONE_BY_ID.get(tone_id)
            if tone is None:
                return
            if self._state.tone_id == tone_id and self._state.select == 1:
                await self.driver.put_property(
                    "case_sound",
                    None,
                    {"transfer_status": "ready", "transfer_progress": "100", "transfer_error": ""},
                    extend_group=True,
                )
                return
            if await self._earbuds_in_case() is False:
                await self._set_transfer_failed(PROMPT_TONE_OTA_HEADSET_OUT_BOX)
                return

            await self.driver.put_property(
                "case_sound",
                None,
                {"transfer_status": "downloading", "transfer_progress": "0", "transfer_error": ""},
                extend_group=True,
            )
            pcm_path = await asyncio.to_thread(self.cache.ensure_pcm, tone)
            pcm_data = await asyncio.to_thread(pcm_path.read_bytes)
            await self.driver.put_property("case_sound", "transfer_status", "transferring")

            self._ota_queue = asyncio.Queue()
            try:
                await self._transfer_tone_ota(tone, pcm_data)
                await self.driver.put_property("case_sound", "transfer_status", "ready")
            except PromptToneTransferError as error:
                log.warning("Prompt tone transfer failed: %s", error)
                await self._set_transfer_failed(error.code, str(error))
            except (TimeoutError, ConnectionResetError, asyncio.TimeoutError) as error:
                log.warning("Prompt tone transfer stopped: %s", error)
                await self._set_transfer_failed(None, "Prompt tone transfer timed out")
            except Exception as error:
                log.exception("Prompt tone transfer failed unexpectedly")
                await self._set_transfer_failed(None, str(error))
            finally:
                self._ota_queue = None

    async def _transfer_tone_ota(self, tone: HuaweiPromptTone, pcm_data: bytes):
        tone_device_id = self._device_id_provider()
        initial_package = build_prompt_tone_package(pcm_data, b"\x00\x00\x00\x00", tone.name)
        start_resp = await self.driver.send_package(
            _ota_start_request(len(initial_package)),
            timeout=15,
        )
        result, mcu_type = _parse_ota_start(start_resp)
        if result != PROMPT_TONE_SUCCESS:
            raise PromptToneTransferError(_format_ota_error(result), result)

        await self._write_state(enabled=True, tone_id=0, tone_device_id=tone_device_id, select=0)

        package = build_prompt_tone_package(pcm_data, mcu_type, tone.name)
        await self.driver.put_property("case_sound", "package_size", str(len(package)))
        prepare_resp = await self.driver.send_package(
            HuaweiSppPackage(CMD_PROMPT_TONE_OTA_PREPARE, resp=CMD_PROMPT_TONE_OTA_PREPARE),
            timeout=10,
        )
        packet_size = _parse_packet_size(prepare_resp)
        if packet_size <= 0:
            raise PromptToneTransferError("Prompt tone packet size was not reported")
        await self.driver.put_property("case_sound", "packet_size", str(packet_size))

        offset_resp = await self.driver.send_package(
            HuaweiSppPackage(CMD_PROMPT_TONE_OTA_READY, [(1, 1)], resp=CMD_PROMPT_TONE_OTA_OFFSET),
            timeout=10,
        )
        last_offset_key = await self._send_requested_packets(offset_resp, package, packet_size)
        repeated_offset_count = 1

        while True:
            event = await self._wait_ota_event()
            if event.command_id == CMD_PROMPT_TONE_OTA_OFFSET:
                offset_key = await self._send_requested_packets(event, package, packet_size)
                if offset_key == last_offset_key:
                    repeated_offset_count += 1
                else:
                    last_offset_key = offset_key
                    repeated_offset_count = 1
                if repeated_offset_count > 3:
                    raise PromptToneTransferError(
                        "Headset keeps requesting the same prompt-tone block; transfer stopped"
                    )
            elif event.command_id == CMD_PROMPT_TONE_OTA_PROGRESS:
                progress = await self._handle_progress(event)
                if progress >= 100:
                    break
            elif event.command_id == CMD_PROMPT_TONE_OTA_ERROR:
                code = _parse_ota_error(event)
                raise PromptToneTransferError(_format_ota_error(code), code)

        if self._transfer_settle_delay > 0:
            await asyncio.sleep(self._transfer_settle_delay)
        await self._write_state(enabled=True, tone_id=tone.tone_id, tone_device_id=tone_device_id, select=1)

    async def _wait_ota_event(self) -> HuaweiSppPackage:
        if self._ota_queue is None:
            raise PromptToneTransferError("Prompt tone transfer queue is not active")
        try:
            async with asyncio.timeout(30):
                return await self._ota_queue.get()
        except (TimeoutError, asyncio.TimeoutError) as error:
            raise PromptToneTransferError("Timed out waiting for prompt-tone transfer event") from error

    async def _send_requested_packets(self, package: HuaweiSppPackage | None, data: bytes, packet_size: int):
        if package is None:
            raise PromptToneTransferError("Prompt tone offset packet was not received")
        offset_location = package.find_param(1)
        retransmission = package.find_param(3)
        if len(offset_location) != 4:
            raise PromptToneTransferError("Prompt tone offset packet is malformed")
        bitmap = retransmission[0] if retransmission else 0
        base_offset = int.from_bytes(offset_location, byteorder="big")

        for packet_index in range(8):
            if bitmap & (1 << packet_index):
                continue
            offset = base_offset + (packet_size * packet_index)
            if offset >= len(data):
                break
            chunk = data[offset:offset + packet_size]
            payload = b"\xff" + offset_location + bytes([packet_index]) + chunk
            await self.driver.send_package(
                HuaweiSppPackage.raw(CMD_PROMPT_TONE_OTA_DATA, payload)
            )
            # Pace raw OTA writes so the headset firmware does not overflow its
            # SPP receive buffer and drop the socket mid-transfer.
            await asyncio.sleep(self._ota_write_delay)
        return offset_location + bytes([bitmap])

    async def _handle_progress(self, package: HuaweiSppPackage) -> int:
        valid_raw = package.find_param(1)
        received_raw = package.find_param(2)
        if len(valid_raw) != 4 or len(received_raw) != 4:
            return 0
        valid_size = int.from_bytes(valid_raw, byteorder="big")
        received_size = int.from_bytes(received_raw, byteorder="big")
        progress = 100 if valid_size <= 0 else min(100, int((received_size / valid_size) * 100))
        await self.driver.put_property("case_sound", "transfer_progress", str(progress))
        return progress

    async def _earbuds_in_case(self) -> bool | None:
        left = await self.driver.get_property("state", "in_box_left")
        right = await self.driver.get_property("state", "in_box_right")
        if left is None or right is None:
            return None
        return left == "true" and right == "true"

    async def _set_transfer_failed(self, code: int | None, message: str | None = None):
        await self.driver.put_property(
            "case_sound",
            None,
            {
                "transfer_status": "failed",
                "transfer_error": message or _format_ota_error(code),
                "transfer_error_code": "" if code is None else str(code),
            },
            extend_group=True,
        )

    @staticmethod
    def _matches_box_tone(package: HuaweiSppPackage) -> bool:
        if package.is_error_response():
            return True
        feature_id = package.find_param(1)
        return len(feature_id) == 1 and feature_id[0] == BOX_TONE_FEATURE_ID


def build_prompt_tone_package(sound_data: bytes, mcu_type: bytes, name: str) -> bytes:
    content = _build_prompt_tone_header(name, len(sound_data)) + sound_data
    header = len(content).to_bytes(4, byteorder="big") + hashlib.sha256(content).digest()
    return header + content + mcu_type


def _build_prompt_tone_header(name: str, sound_size: int) -> bytes:
    name_bytes = _fixed_name(name)
    metadata = _le16(15470) + b"\x00\x10\x00\x01" + _le32(sound_size // 16) + name_bytes
    checksum = crc16_xmodem(metadata)[::-1]
    return checksum + metadata + _le32(64000) + name_bytes


def _fixed_name(name: str) -> bytes:
    raw = name.encode("utf-8")[:32]
    return raw + (b"\x00" * (32 - len(raw)))


def _le16(value: int) -> bytes:
    return bytes([value & 0xff, (value >> 8) & 0xff])


def _le32(value: int) -> bytes:
    return bytes([
        value & 0xff,
        (value >> 8) & 0xff,
        (value >> 16) & 0xff,
        (value >> 24) & 0xff,
    ])


def _ota_start_request(package_size: int) -> HuaweiSppPackage:
    return HuaweiSppPackage(
        CMD_PROMPT_TONE_OTA_START,
        [
            (1, b"\x01"),
            (2, b"\x00\x00"),
            (3, b"\x00"),
            (6, b"\x04"),
            (9, package_size.to_bytes(4, byteorder="big")),
            (10, b"\x00"),
        ],
        resp=CMD_PROMPT_TONE_OTA_START,
    )


def _parse_ota_start(package: HuaweiSppPackage | None) -> tuple[int, bytes]:
    if package is None:
        raise RuntimeError("Prompt tone transfer did not start")
    result_raw = package.find_param(127)
    result = int.from_bytes(result_raw, byteorder="big") if result_raw else 0
    mcu_type = package.find_param(11)
    if not mcu_type:
        mcu_type = b"\x00\x00\x00\x00"
    return result, mcu_type


def _parse_packet_size(package: HuaweiSppPackage | None) -> int:
    if package is None:
        return 0
    raw = package.find_param(3)
    if len(raw) != 2:
        return 0
    return int.from_bytes(raw, byteorder="big") - 9


def _parse_ota_error(package: HuaweiSppPackage) -> int:
    raw = package.find_param(127)
    return int.from_bytes(raw, byteorder="big") if raw else -1


def _format_ota_error(code: int | None) -> str:
    if code is None:
        return "Prompt tone transfer failed"
    return PROMPT_TONE_ERROR_MESSAGES.get(code, f"Prompt tone transfer failed: {code}")


def _local_tone_device_id() -> str:
    value = uuid.getnode() & 0xffffffffffff
    return f"{value:012X}"
