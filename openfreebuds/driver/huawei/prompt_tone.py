"""充电盒提示音：本地/云端配置解析与音频转换。

配置 schema（version 3）：data 为内置/自定义提示音，officialData 为需下载的官方提示音，
条目字段 id/name/zhCn/support。

音频口径有两套，别混：
- **播放/打包口径（APK 原始数据，不可改动）**：`TONE_PACKAGE_RATE=16000`（整包内层第 44–48
  字节的固定字段）、`TONE_MAX_SECONDS=6`、`TONE_MAX_BYTES=16000*2*6=192000`。
- **实际产出的 PCM 口径**：`TONE_SAMPLE_RATE=16755`（设备实测以此速率播放）。所以 192000
  字节在 16755Hz 下只够 `TONE_MAX_DURATION ≈ 5.73s`，除以 16000 才是 6s。
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

TONE_SAMPLE_RATE = 16755        # 产出 PCM 的采样率（设备实测播放速率）
TONE_PACKAGE_RATE = 16000       # 整包内层头里的固定字段值（APK 原样，勿动）
TONE_MAX_SECONDS = 6            # APK 给的时长上限，按 16000 基准算
TONE_MAX_BYTES = TONE_PACKAGE_RATE * 2 * TONE_MAX_SECONDS   # = 192000，APK 原始封顶
TONE_MAX_SAMPLES = TONE_MAX_BYTES // 2                       # = 96000 个样本
TONE_MAX_DURATION = TONE_MAX_SAMPLES / TONE_SAMPLE_RATE      # ≈ 5.7298s（16755Hz 下的实际可用时长）
TONE_PEAK = int(0.8 * 32767)
# 自动增益的满响度基准：就是 APK 的归一化峰值（0.8 满刻度）。
# 这个值是官方工程师调试后定的，超过它设备侧就可能爆电平，所以不做「顶到 32767」。
TONE_AUTO_GAIN_TARGET = TONE_PEAK

CLOUD_BASE = "https://smarthome-drcn.dbankcdn.cn/device/guide/AAM001"

# 100–179 是随包预置、但性质上属于用户可改/可删的自定义提示音；界面和库操作
# 不再把它们单列为「内置自定义音效」。
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
    # 用户自定义的显示名（config 里的 displayName）；官方条目不写这个字段，
    # 显示名由官方 zhCn / PromptToneName 翻译词典提供
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
    """读取随包内置的提示音目录（openfreebuds/assets/tone_config.json）。"""
    path = Path(__file__).resolve().parents[2] / "assets" / "tone_config.json"
    return parse_tone_config(json.loads(path.read_text(encoding="utf-8")))


def fetch_cloud_resources(cache_dir: Path, model: str = "00000A",
                          force: bool = False) -> tuple[list[ToneEntry], Path]:
    """下载并解压云端 promptToneConfig / promptTone 包，返回 (配置条目, 官方PCM目录)。"""
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
    """用户/系统 PATH（注册表里的真值）。

    进程可能被一个被裁剪过 PATH 的父进程拉起来（例如各种 GUI 启动器、沙箱），
    这时 shutil.which 找不到已安装的 ffmpeg，但注册表里的 PATH 仍然是对的。
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
    """定位 ffmpeg：环境变量 OFB_FFMPEG → PATH → 注册表 PATH → 常见安装位置。"""
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
    """没有 ffmpeg 时的兜底：用标准库 wave 读 WAV，重采样到 TONE_SAMPLE_RATE。"""
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
    """任意音频 -> Signed 16bit 16755Hz Mono 小端样本数组（int16）。

    max_seconds 只限制解码时长（默认不限制，调用方按需要截断），用于裁剪界面的波形数据。
    优先用 ffmpeg（支持 wav/mp3/flac/ogg/m4a/aac）；ffmpeg 不在时，WAV 走标准库兜底。
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
    """把这段音频的峰值刚好抬到满响度（默认 26213 = APK 归一化峰值）所需的增益（dB）。

    空音频或全零返回 0.0；这是「不爆电平」的最佳增益：官方调试定的 0.8 满刻度上限。
    """
    data = np.asarray(samples, dtype=np.int32)
    peak = int(np.max(np.abs(data))) if data.size else 0
    if peak <= 0:
        return 0.0
    return 20.0 * float(np.log10(target / peak))


def apply_gain_db(samples: np.ndarray, gain_db: float) -> np.ndarray:
    """按 dB 增益缩放样本；超过 int16 范围的按满刻度硬限幅（避免回绕成反相噪声）。"""
    data = np.asarray(samples, dtype=np.float64) * (10.0 ** (float(gain_db) / 20.0))
    return np.clip(np.rint(data), -32768, 32767).astype("<i2")


def encode_tone_pcm(samples: np.ndarray, dst: Path, normalize: bool = True) -> None:
    """样本 -> 提示音 PCM，按 APK 的 192000 字节封顶截断后校验。

    normalize=True（默认）：峰值归一到 0.8*32767，等同「自动增益」；
    normalize=False：保留样本现有电平（调用方已按用户设定做过增益），只做截断与校验。
    """
    samples = np.asarray(samples, dtype="<i2")[:TONE_MAX_SAMPLES]
    if normalize:
        peak = int(np.max(np.abs(samples.astype(np.int32)))) if samples.size else 0
        if peak > 0:
            samples = (samples.astype(np.float64) * (TONE_PEAK / peak)).astype("<i2")
    dst.write_bytes(samples.tobytes())
    validate_tone_pcm(dst)


def convert_to_tone_pcm(src: Path, dst: Path) -> None:
    """任意音频 -> Signed 16bit 16755Hz Mono 小端 PCM，按 192000 字节封顶后峰值归一。

    源文件本身已经是提示音 PCM（本地库里就是这种）时直接搬运，不走解码——
    否则会被当成未知格式，在没有 ffmpeg 的机器上直接失败。
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
    """自定义提示音整包：outer36(总长4BE+SHA256) + inner48 + PCM + mcuType。

    inner 布局按 2026-11-14 官方 App 真机抓包校正（交接文档 §10.4）：
        CRC16(core)(2LE) + core(2+4+4) + rate(4LE, 固定 16000) + name(32B)
    → 共 48 字节。core 里**不含** name（旧版重复了一次 name，导致 inner=80，是错的）。
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