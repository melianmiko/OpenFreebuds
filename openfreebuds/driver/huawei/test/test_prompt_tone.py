import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pytest

from openfreebuds.driver.huawei import prompt_tone as pt


def test_parse_tone_config():
    raw = {
        "version": 3,
        "data": [{"id": 0, "name": "Unfold", "zhCn": "舒展"},
                 {"id": 109, "name": "cliip", "zhCn": "恶夹式恶机"}],
        "officialData": [{"id": 200, "name": "Chopin", "zhCn": "肖邦", "support": "00016D_19"}],
    }
    entries = pt.parse_tone_config(raw)
    assert [e.id for e in entries] == [0, 109, 200]
    assert entries[0].display_name == "舒展"
    assert entries[1].official is False
    assert entries[2].official is True
    assert entries[2].support == "00016D_19"


def test_parse_tone_config_display_fallback():
    entries = pt.parse_tone_config({"data": [{"id": 1, "name": "X"}]})
    assert entries[0].display_name == "X"
    assert entries[0].zh_cn == ""


def test_parse_tone_config_display_name_wins():
    """自定义层写 displayName：显示名优先，且不再看 zhCn。"""
    entries = pt.parse_tone_config({
        "data": [{"id": 50, "name": "MyChime", "displayName": "我的铃声",
                  "support": "custom"}],
    })
    assert entries[0].display_name == "我的铃声"
    assert entries[0].name == "MyChime"


def test_load_local_config(tmp_path):
    (tmp_path / "tone_config.json").write_text(
        json.dumps({"version": 3, "data": [{"id": 4, "name": "Bongo", "zhCn": "邦戈手鼓"}]}),
        encoding="utf-8")
    entries = pt.load_local_config(tmp_path)
    assert entries == [pt.ToneEntry(4, "Bongo", "邦戈手鼓")]


def test_fetch_cloud_resources_from_cache(tmp_path):
    cfg = {"version": 3, "data": [{"id": 0, "name": "Unfold", "zhCn": "舒展"}], "officialData": []}
    for key in ("promptToneConfig", "promptTone"):
        with zipfile.ZipFile(tmp_path / f"00000A_{key}.zip", "w") as z:
            z.writestr(f"00000A_{key}/tone_config.json", json.dumps(cfg))
            if key == "promptTone":
                z.writestr("00000A_promptTone/Unfold.pcm", b"\x00\x01" * 100)
    entries, tones_dir = pt.fetch_cloud_resources(tmp_path)
    assert entries[0].id == 0
    assert (tones_dir / "Unfold.pcm").exists()


def test_tone_limits():
    """容量口径以 APK 原始数据为准（16000 基准 6s = 192000），与 PCM 采样率 16755 解耦。"""
    assert pt.TONE_PACKAGE_RATE == 16000
    assert pt.TONE_SAMPLE_RATE == 16755
    assert pt.TONE_MAX_BYTES == 192000
    assert pt.TONE_MAX_BYTES == pt.TONE_PACKAGE_RATE * 2 * pt.TONE_MAX_SECONDS
    assert abs(pt.TONE_MAX_DURATION - 192000 / 2 / 16755) < 1e-9
    assert pt.TONE_MAX_DURATION < pt.TONE_MAX_SECONDS


def test_encode_trims_to_max_bytes(tmp_path):
    dst = tmp_path / "trim.pcm"
    pt.encode_tone_pcm(np.zeros(pt.TONE_MAX_SAMPLES + 1234, dtype="<i2"), dst)
    assert dst.stat().st_size == pt.TONE_MAX_BYTES


def test_validate_tone_pcm(tmp_path):
    ok = tmp_path / "ok.pcm"
    ok.write_bytes(b"\x00\x01" * 1000)
    pt.validate_tone_pcm(ok)

    odd = tmp_path / "odd.pcm"
    odd.write_bytes(b"\x00")
    with pytest.raises(ValueError):
        pt.validate_tone_pcm(odd)

    empty = tmp_path / "empty.pcm"
    empty.write_bytes(b"")
    with pytest.raises(ValueError):
        pt.validate_tone_pcm(empty)

    big = tmp_path / "big.pcm"
    big.write_bytes(b"\x00" * (pt.TONE_MAX_BYTES + 2))
    with pytest.raises(ValueError):
        pt.validate_tone_pcm(big)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_convert_to_tone_pcm(tmp_path):
    src = tmp_path / "src.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=7", str(src)],
                   check=True, capture_output=True)
    dst = tmp_path / "dst.pcm"
    pt.convert_to_tone_pcm(src, dst)
    assert dst.stat().st_size == pt.TONE_MAX_BYTES
    samples = np.frombuffer(dst.read_bytes(), dtype="<i2")
    assert abs(int(np.max(np.abs(samples.astype(np.int32)))) - pt.TONE_PEAK) <= 1


def _write_wav(path, rate=44100, channels=2, seconds=1.5):
    import wave
    frames = int(rate * seconds)
    data = (np.sin(np.arange(frames) / 20.0) * 9000).astype("<i2")
    if channels > 1:
        data = np.repeat(data[:, None], channels, axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data.tobytes())


def test_find_ffmpeg_env(tmp_path, monkeypatch):
    exe = tmp_path / "ffmpeg.exe"
    exe.write_bytes(b"")
    monkeypatch.setenv("OFB_FFMPEG", str(exe))
    assert pt.find_ffmpeg() == str(exe)


def test_decode_wav_without_ffmpeg(tmp_path, monkeypatch):
    monkeypatch.setattr(pt, "find_ffmpeg", lambda: None)
    src = tmp_path / "src.wav"
    _write_wav(src, rate=44100, channels=2, seconds=1.5)
    samples = pt.decode_audio(src)
    assert samples.dtype == np.int16
    assert abs(samples.size / pt.TONE_SAMPLE_RATE - 1.5) < 0.02
    with pytest.raises(RuntimeError):
        other = tmp_path / "src.mp3"
        other.write_bytes(b"\x00")
        pt.decode_audio(other)


def test_crc16_xmodem():
    assert pt.crc16_xmodem(b"123456789") == 0x31C3


def test_build_tone_package():
    """inner 按 2026-11-14 官方 App 真机抓包：CRC2 + core10 + rate4 + name32 = 48 字节。"""
    pcm = b"\x01\x02" * 1600
    pkg = pt.build_tone_package(pcm, "test", b"\x00\x00\x00\x00")
    assert len(pkg) == 36 + 48 + len(pcm) + 4
    assert int.from_bytes(pkg[0:4], "big") == 48 + len(pcm)
    assert pkg[4:36] == hashlib.sha256(pkg[36:36 + 48 + len(pcm)]).digest()
    inner = pkg[36:36 + 48]
    assert inner[2:4] == b"\x6e\x3c"
    assert inner[4:8] == bytes([0x00, 0x10, 0x00, 0x01])
    assert int.from_bytes(inner[8:12], "little") == len(pcm) // 16
    assert int.from_bytes(inner[12:16], "little") == pt.TONE_PACKAGE_RATE
    assert inner[16:48] == b"test".ljust(32, b"\x00")
    assert pt.TONE_SAMPLE_RATE == 16755
    assert pt.TONE_PACKAGE_RATE == 16000
    assert int.from_bytes(inner[0:2], "little") == pt.crc16_xmodem(inner[2:12])
    assert pkg[-4:] == b"\x00\x00\x00\x00"
    with pytest.raises(ValueError):
        pt.build_tone_package(b"\x00" * (pt.TONE_MAX_BYTES + 2), "x")

def test_convert_pcm_passthrough(tmp_path):
    """本地库里的 .pcm 已经是目标格式，必须直接搬运，不能再去解码（无 ffmpeg 时那会直接失败）。"""
    src = tmp_path / "lib.pcm"
    src.write_bytes(b"\x01\x02" * 100)
    dst = tmp_path / "out.pcm"
    pt.convert_to_tone_pcm(src, dst)
    assert dst.read_bytes() == src.read_bytes()

    too_big = tmp_path / "big.pcm"
    too_big.write_bytes(b"\x00\x00" * (pt.TONE_MAX_BYTES // 2 + 10))
    pt.convert_to_tone_pcm(too_big, dst)
    assert dst.stat().st_size == pt.TONE_MAX_BYTES


def test_peak_gain_db_reaches_headroom():
    """自动增益：把峰值刚好抬到满响度（26213 = APK 归一化峰值，0.8 满刻度）所需的 dB。"""
    samples = np.array([0, 1000, -1000], dtype="<i2")
    expected = 20 * np.log10(pt.TONE_AUTO_GAIN_TARGET / 1000)
    assert abs(pt.peak_gain_db(samples) - expected) < 1e-6
    assert abs(pt.peak_gain_db(samples, target=32767)
               - 20 * np.log10(32767 / 1000)) < 1e-6
    assert pt.peak_gain_db(np.zeros(10, dtype="<i2")) == 0.0
    # 已归一到 26213 的音频已在满响度，最佳增益就是 0；更低的才给正增益
    assert abs(pt.peak_gain_db(np.array([pt.TONE_PEAK], dtype="<i2"))) < 1e-9
    assert pt.peak_gain_db(np.array([6500], dtype="<i2")) > 10.0


def test_apply_gain_db_scales_and_clips():
    samples = np.array([100, -200, 300], dtype="<i2")
    doubled = pt.apply_gain_db(samples, 6.0206)   # +6 dB ≈ x2
    assert doubled.tolist() == [200, -400, 600]
    # 超过满刻度时硬限幅，不回绕成反相噪声
    loud = pt.apply_gain_db(np.array([20000, -20000], dtype="<i2"), 12.0)
    assert loud.tolist() == [32767, -32768]


def test_encode_without_normalize_keeps_gain(tmp_path):
    """取消归一：手动增益后的电平必须原样落盘，不能被再拉回 0.8 满刻度。"""
    samples = (np.ones(1000) * 5000).astype("<i2")
    dst = tmp_path / "quiet.pcm"
    pt.encode_tone_pcm(samples, dst, normalize=False)
    peak = int(np.max(np.abs(np.frombuffer(dst.read_bytes(), dtype="<i2").astype(np.int32))))
    assert peak == 5000

    # 默认仍走归一（旧的导入路径行为不变）
    auto = tmp_path / "auto.pcm"
    pt.encode_tone_pcm(samples, auto, normalize=True)
    peak = int(np.max(np.abs(np.frombuffer(auto.read_bytes(), dtype="<i2").astype(np.int32))))
    assert abs(peak - pt.TONE_PEAK) <= 1