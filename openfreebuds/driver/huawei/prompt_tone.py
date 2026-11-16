"""Charging-case prompt tones: local/cloud config parsing and audio conversion.

Config schema version 3: data contains built-in/custom tones, officialData contains downloadable official tones; entries use id/name/zhCn/support. Two audio rate conventions must not be mixed: the APK packaging/playback rate (16000) and the actual PCM sample rate (16755).
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
import urllib.request
import wave
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

TONE_SAMPLE_RATE = 16755        # PCM sample rate produced here (measured device playback rate)
TONE_PACKAGE_RATE = 16000       # Fixed values inside the packet header (copied from the APK; do not change)
TONE_MAX_SECONDS = 6            # Duration limit from the APK, based on 16000
TONE_MAX_BYTES = TONE_PACKAGE_RATE * 2 * TONE_MAX_SECONDS   # = 192000, the APK's original cap
TONE_MAX_SAMPLES = TONE_MAX_BYTES // 2                       # = 96000 samples
TONE_MAX_DURATION = TONE_MAX_SAMPLES / TONE_SAMPLE_RATE      # about 5.7298 s at 16755 Hz, the actual usable duration
TONE_PEAK = int(0.8 * 32767)
# Full-scale reference for auto gain: the APK normalized peak (0.8 full scale).
# Official engineers chose this value; exceeding it may clip on the device, so do not normalize to 32767.
TONE_AUTO_GAIN_TARGET = TONE_PEAK

CLOUD_BASE = "https://smarthome-drcn.dbankcdn.cn/device/guide/AAM001"

# 100-179 are bundled but behave as user-editable/deletable custom tones; the UI and library
# no longer list them separately as built-in custom effects.
PRESET_CUSTOM_ID_RANGES = ((100, 179),)


def is_custom_tone_id(tone_id: int) -> bool:
    return any(start <= int(tone_id) <= end for start, end in PRESET_CUSTOM_ID_RANGES)


@dataclass(frozen=True)
class ToneEntry:
    id: int
    name: str
    zh_cn: str
    official: bool = False
    support: str = ""
    # User-defined display name (displayName in config); official entries omit it,
    # their names come from the official zhCn / PromptToneName dictionary
    display: str = ""

    @property
    def display_name(self) -> str:
        return self.display or self.zh_cn or self.name


def parse_tone_config(raw: dict) -> list[ToneEntry]:
    entries = []
    for official, key in ((False, "data"), (True, "officialData")):
        for item in raw.get(key, []):
            entries.append(ToneEntry(
                id=int(item["id"]),
                name=item["name"],
                zh_cn=item.get("zhCn", ""),
                official=official,
                support=item.get("support", ""),
                display=item.get("displayName", ""),
            ))
    return entries


def load_local_config(config_dir: Path) -> list[ToneEntry]:
    raw = json.loads((config_dir / "tone_config.json").read_text(encoding="utf-8"))
    return parse_tone_config(raw)


def load_builtin_config() -> list[ToneEntry]:
    """Read the bundled tone catalog from openfreebuds/assets/tone_config.json."""
    path = Path(__file__).resolve().parents[2] / "assets" / "tone_config.json"
    return parse_tone_config(json.loads(path.read_text(encoding="utf-8")))


def fetch_cloud_resources(cache_dir: Path, model: str = "00000A",
                          force: bool = False) -> tuple[list[ToneEntry], Path]:
    """Download and unpack the cloud promptToneConfig / promptTone packages; return (config entries, official PCM directory)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    tones_dir = cache_dir / f"{model}_promptTone"
    for key in ("promptToneConfig", "promptTone"):
        zip_path = cache_dir / f"{model}_{key}.zip"
        if force or not zip_path.exists():
            url = f"{CLOUD_BASE}/{model}/{model}_{key}.zip"
            urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(cache_dir)
    entries = load_local_config(cache_dir / f"{model}_promptToneConfig")
    return entries, tones_dir


FFMPEG_CANDIDATES = (
    r"C:\ffmpeg\bin\ffmpeg.exe",
    r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
    r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe",
    r"%USERPROFILE%\scoop\shims\ffmpeg.exe",
    r"%LOCALAPPDATA%\Programs\ffmpeg\bin\ffmpeg.exe",
)


def _registry_path_dirs() -> list[Path]:
    """User/system PATH (the real value from the registry).
    The process may be started by a parent with a trimmed PATH (GUI launchers, sandboxes), so shutil.which may miss an installed ffmpeg while the registry PATH is still correct.
    """
    try:
        import winreg
    except ImportError:
        return []
    dirs: list[Path] = []
    for root, sub in (
        (winreg.HKEY_CURRENT_USER, r"Environment"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
    ):
        try:
            with winreg.OpenKey(root, sub) as key:
                raw, _ = winreg.QueryValueEx(key, "Path")
        except OSError:
            continue
        for item in str(raw).split(";"):
            item = item.strip()
            if item and "%" not in item:
                dirs.append(Path(item))
    return dirs


def find_ffmpeg() -> str | None:
    """Locate ffmpeg: OFB_FFMPEG -> PATH -> registry PATH -> common install locations."""
    env = os.environ.get("OFB_FFMPEG")
    if env and Path(env).is_file():
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    for directory in _registry_path_dirs():
        exe = directory / "ffmpeg.exe"
        try:
            if exe.is_file():
                return str(exe)
        except OSError:
            continue
    for candidate in FFMPEG_CANDIDATES:
        path = Path(os.path.expandvars(candidate))
        if path.is_file():
            return str(path)
    return None


def _decode_wav_samples(src: Path, max_seconds: float | None = None) -> np.ndarray:
    """Fallback without ffmpeg: read WAV with the standard library wave module and resample to TONE_SAMPLE_RATE."""
    with wave.open(str(src), "rb") as wav:
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())
    if width != 2:
        raise RuntimeError("只支持 16bit WAV，请安装 ffmpeg 以转换其它格式")
    if max_seconds is not None:
        frames = frames[:int(max_seconds * rate) * channels * 2]
    data = np.frombuffer(frames, dtype="<i2").astype(np.float64)
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    if rate != TONE_SAMPLE_RATE and data.size:
        count = int(round(data.size * TONE_SAMPLE_RATE / rate))
        data = np.interp(np.linspace(0, data.size - 1, count),
                         np.arange(data.size), data)
    return np.clip(data, -32768, 32767).astype("<i2")


def decode_audio(src: Path, max_seconds: float | None = None) -> np.ndarray:
    """Any audio -> signed 16-bit 16755 Hz mono little-endian int16 samples.
    max_seconds limits decode duration only (unlimited by default; callers truncate as needed) and is used for waveform data in the editor. Prefer ffmpeg (wav/mp3/flac/ogg/m4a/aac); fall back to the standard-library WAV path when ffmpeg is absent.
    """
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        if src.suffix.lower() == ".wav":
            return _decode_wav_samples(src, max_seconds)
        raise RuntimeError(
            "未找到 ffmpeg，无法转换该音频格式（WAV 可直接导入）。"
            "请安装 ffmpeg 或设置环境变量 OFB_FFMPEG 指向 ffmpeg.exe")
    fd, tmp_name = tempfile.mkstemp(suffix=".raw", prefix="ofb_tone_")
    os.close(fd)
    tmp = Path(tmp_name)
    args = [ffmpeg, "-y", "-i", str(src)]
    if max_seconds is not None:
        args += ["-t", str(max_seconds)]
    args += ["-ar", str(TONE_SAMPLE_RATE), "-ac", "1", "-f", "s16le", str(tmp)]
    subprocess.run(args, check=True, capture_output=True)
    try:
        return np.frombuffer(tmp.read_bytes(), dtype="<i2").astype(np.int16)
    finally:
        if tmp.exists():
            tmp.unlink()


def peak_gain_db(samples: np.ndarray, target: int = TONE_AUTO_GAIN_TARGET) -> float:
    """Gain in dB needed to raise this audio's peak exactly to full scale (default 26213 = APK normalized peak).
    Empty or all-zero audio returns 0.0; this is the 'no clipping' best gain at the official 0.8 full-scale ceiling.
    """
    data = np.asarray(samples, dtype=np.int32)
    peak = int(np.max(np.abs(data))) if data.size else 0
    if peak <= 0:
        return 0.0
    return 20.0 * float(np.log10(target / peak))


def apply_gain_db(samples: np.ndarray, gain_db: float) -> np.ndarray:
    """Scale samples by dB gain and hard-limit to the int16 range at full scale (avoid wrap-around into inverted noise)."""
    data = np.asarray(samples, dtype=np.float64) * (10.0 ** (float(gain_db) / 20.0))
    return np.clip(np.rint(data), -32768, 32767).astype("<i2")


def encode_tone_pcm(samples: np.ndarray, dst: Path, normalize: bool = True) -> None:
    """Samples -> prompt-tone PCM, truncated and validated against the APK's 192000-byte cap.
    normalize=True (default): normalize the peak to 0.8*32767, equivalent to auto gain; normalize=False: keep the current level (the caller already applied user gain) and only truncate/validate.
    """
    samples = np.asarray(samples, dtype="<i2")[:TONE_MAX_SAMPLES]
    if normalize:
        peak = int(np.max(np.abs(samples.astype(np.int32)))) if samples.size else 0
        if peak > 0:
            samples = (samples.astype(np.float64) * (TONE_PEAK / peak)).astype("<i2")
    dst.write_bytes(samples.tobytes())
    validate_tone_pcm(dst)


def convert_to_tone_pcm(src: Path, dst: Path) -> None:
    """Any audio -> signed 16-bit 16755 Hz mono little-endian PCM, capped at 192000 bytes and peak-normalized.
    If the source is already prompt-tone PCM (as in the local library), copy it directly instead of decoding; otherwise it would be treated as an unknown format and fail on machines without ffmpeg.
    """
    if src.suffix.lower() == ".pcm":
        data = src.read_bytes()[:TONE_MAX_BYTES]
        dst.write_bytes(data)
        validate_tone_pcm(dst)
        return
    samples = decode_audio(src, TONE_MAX_DURATION + 0.5)
    encode_tone_pcm(samples, dst)


def validate_tone_pcm(path: Path) -> None:
    size = path.stat().st_size
    if size == 0 or size % 2 != 0:
        raise ValueError(f"PCM 数据无效: {path.name} ({size} bytes)")
    if size > TONE_MAX_BYTES:
        raise ValueError(f"提示音超过 {TONE_MAX_BYTES} 字节上限: {path.name} ({size} bytes)")


def crc16_xmodem(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def build_tone_package(pcm: bytes, name: str, mcu_type: bytes = b"\x00\x00\x00\x00") -> bytes:
    """Custom prompt-tone package: outer36 (total length 4BE + SHA256) + inner48 + PCM + mcuType.
    The inner layout follows the official App capture on 2026-11-14 (handoff doc section 10.4): CRC16(core)(2LE) + core(2+4+4) + rate(4LE, fixed 16000) + name(32B), 48 bytes total.
    """
    if len(pcm) == 0 or len(pcm) % 2 != 0 or len(pcm) > TONE_MAX_BYTES:
        raise ValueError(f"PCM 数据无效: {len(pcm)} bytes")
    name_b = name.encode("utf-8")[:32].ljust(32, b"\x00")
    core = (struct.pack("<H", 0x3C6E) + bytes([0x00, 0x10, 0x00, 0x01])
            + struct.pack("<I", len(pcm) // 16))
    inner = (struct.pack("<H", crc16_xmodem(core)) + core
             + struct.pack("<I", TONE_PACKAGE_RATE) + name_b)
    body = inner + pcm
    return struct.pack(">I", len(body)) + hashlib.sha256(body).digest() + body + mcu_type