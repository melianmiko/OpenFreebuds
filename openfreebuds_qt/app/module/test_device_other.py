"""Unit tests for preview-audio lifecycle hooks outside a full main window."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace

from openfreebuds_qt.app.module.device_other import OfbQtDeviceOtherSettingsModule


class _FakePlayer:
    def __init__(self):
        self.calls = []

    def stop(self):
        self.calls.append("stop")

    def setSource(self, source):
        self.calls.append(source)


def test_stop_preview_audio_stops_player_and_removes_temp_file(tmp_path):
    preview = tmp_path / "preview.wav"
    preview.write_bytes(b"RIFF")

    player = _FakePlayer()
    fake = SimpleNamespace(_preview_player=player, _preview_tmp=preview)

    OfbQtDeviceOtherSettingsModule.stop_preview_audio(fake)

    assert player.calls[0] == "stop"
    assert len(player.calls) == 2
    assert not preview.exists()
    assert fake._preview_tmp is None
