"""
Huawei prompt-tone resources.

Kept apart from the SPP handler in openfreebuds.driver.huawei.handler.prompt_tone
so the device-facing protocol code is not mixed with the download/verification
of the resource archives from Huawei's CDN.
"""

import asyncio
import hashlib
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

import aiohttp

from openfreebuds.constants import STORAGE_PATH
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiPromptToneResources")

PROMPT_TONE_SUCCESS = 100000

# CDN path is region scoped
PROMPT_TONE_CDN_LANGUAGE = os.getenv("OFB_PROMPT_TONE_LANGUAGE", "ru")
PROMPT_TONE_CDN_ROOT = (
    "https://contentcenter-drru.dbankcdn.ru/pub_1/"
    "HW-SmartHome_oem_900_9/43/v3/"
    f"{PROMPT_TONE_CDN_LANGUAGE}/device/guide/00000A"
)
PROMPT_TONE_CONFIG_URL = f"{PROMPT_TONE_CDN_ROOT}/00000A_promptToneConfig.zip"
PROMPT_TONE_ARCHIVE_URL = f"{PROMPT_TONE_CDN_ROOT}/00000A_promptTone.zip"

# PCM is flashed as-is, so check digests before extracting anything
PROMPT_TONE_CONFIG_SHA256 = "6f9e998a48a37bf16952fd73e2e4cbb4cb0a6810bf54a7700a4c89694cd5337f"
PROMPT_TONE_ARCHIVE_SHA256 = "fda388b48339abf10dc201246e450ae0973cfb7e0625a23210676b121285376c"

# Archives are under a megabyte, this is just an upper bound
PROMPT_TONE_MAX_DOWNLOAD_SIZE = 8 * 1024 * 1024
PROMPT_TONE_DOWNLOAD_TIMEOUT = 60

_CHUNK_SIZE = 1024 * 1024


class PromptToneTransferError(RuntimeError):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class PromptToneResourceError(PromptToneTransferError):
    """
    Raised when downloaded prompt-tone resources can't be trusted.
    """


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


class HuaweiPromptToneResourceCache:
    """
    Downloads and unpacks the prompt-tone archives from Huawei's CDN.

    Zip and disk work runs on worker threads, so the driver's event loop keeps
    talking to the headset while the resources are fetched.
    """

    def __init__(self, root: Path | None = None):
        self.root = root or STORAGE_PATH / "huawei_prompt_tones" / "00000A"
        self.config_zip_path = self.root / "00000A_promptToneConfig.zip"
        self.archive_zip_path = self.root / "00000A_promptTone.zip"
        self.config_path = self.root / "tone_config.json"
        self.pcm_root = self.root / "pcm"

    async def prepare(self):
        await asyncio.to_thread(self.root.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(self.pcm_root.mkdir, parents=True, exist_ok=True)
        await self._ensure_zip(PROMPT_TONE_CONFIG_URL, self.config_zip_path, PROMPT_TONE_CONFIG_SHA256)
        await self._ensure_zip(PROMPT_TONE_ARCHIVE_URL, self.archive_zip_path, PROMPT_TONE_ARCHIVE_SHA256)
        await asyncio.to_thread(self._extract_config)
        await asyncio.to_thread(self._extract_pcm_files)

    async def ensure_pcm(self, tone: HuaweiPromptTone) -> Path:
        path = self.pcm_root / tone.file_name
        if not await asyncio.to_thread(path.is_file):
            await self.prepare()
        if not await asyncio.to_thread(path.is_file):
            raise FileNotFoundError(f"Prompt tone PCM not found in Huawei resource cache: {tone.file_name}")
        return path

    async def _ensure_zip(self, url: str, path: Path, expected_sha256: str):
        if await asyncio.to_thread(path.is_file):
            if await asyncio.to_thread(self._file_sha256, path) == expected_sha256:
                return
            log.warning("Cached prompt tone archive %s failed verification, re-downloading", path.name)
            await asyncio.to_thread(path.unlink)

        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            digest = await self._download(url, tmp_path)
            actual = digest.hexdigest()
            if actual != expected_sha256:
                raise PromptToneResourceError(
                    f"Prompt tone archive {path.name} failed integrity check "
                    f"(expected {expected_sha256}, got {actual})"
                )

            await asyncio.to_thread(tmp_path.replace, path)
        except BaseException:
            await asyncio.to_thread(tmp_path.unlink, missing_ok=True)
            raise

    async def _download(self, url: str, target: Path) -> "hashlib._Hash":
        digest = hashlib.sha256()
        downloaded = 0
        timeout = aiohttp.ClientTimeout(total=PROMPT_TONE_DOWNLOAD_TIMEOUT)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with open(target, "wb") as file:
                    async for chunk in response.content.iter_chunked(_CHUNK_SIZE):
                        downloaded += len(chunk)
                        if downloaded > PROMPT_TONE_MAX_DOWNLOAD_SIZE:
                            raise PromptToneResourceError(
                                f"Prompt tone archive {target.name} exceeds the "
                                f"{PROMPT_TONE_MAX_DOWNLOAD_SIZE} byte limit"
                            )
                        digest.update(chunk)
                        file.write(chunk)

        return digest

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as file:
            for chunk in iter(lambda: file.read(_CHUNK_SIZE), b""):
                digest.update(chunk)
        return digest.hexdigest()

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