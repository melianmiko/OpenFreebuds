"""Offscreen tests for the loudness-gain control: sync, disabling, no rollback, and gain actually applied to samples."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PyQt6")
from PyQt6.QtWidgets import QApplication

from openfreebuds.driver.huawei.prompt_tone import TONE_AUTO_GAIN_TARGET
from openfreebuds_qt.app.dialog.tone_editor import OfbQtToneEditorDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def dialog(app):
    samples = (np.sin(np.arange(8000) / 30.0) * 4000).astype("<i2")
    dlg = OfbQtToneEditorDialog(None, samples)
    yield dlg
    dlg.cleanup()


def test_auto_gain_is_default_and_disables_manual_controls(dialog):
    assert dialog.auto_gain is True
    assert dialog.gain_slider.isEnabled() is False
    assert dialog.gain_box.isEnabled() is False

    peak = int(np.max(np.abs(dialog.selection.astype(np.int32))))
    expected = 20 * np.log10(TONE_AUTO_GAIN_TARGET / peak)
    assert abs(dialog.gain_db - expected) < 0.02
    # The same value must appear in both the slider and the spin box, and the waveform redraws from it
    assert abs(dialog.gain_box.value() - expected) < 0.02
    assert abs(dialog.gain_slider.value() - expected) < 0.01
    assert abs(dialog.waveform.gain_db - expected) < 0.01


def test_unchecking_keeps_best_value_instead_of_restoring(dialog):
    dialog.auto_gain_check.setChecked(False)
    dialog.gain_box.setValue(6.0)
    dialog.gain_slider.setValue(6.0, emit=True)
    assert dialog.gain_db == 6.0

    auto_value = dialog.gain_box.value() + 0  # Record the value before checking, for comparison only
    dialog.auto_gain_check.setChecked(True)     # Checked: fill in the best gain and disable the controls
    best = dialog.gain_db
    assert best != 6.0
    assert dialog.gain_box.isEnabled() is False
    # After checking, the displayed value must really change (the previous bug was a missing refresh here)
    assert abs(dialog.gain_box.value() - 6.0) > 0.1
    assert abs(dialog.gain_slider.value() - 6.0) > 0.1

    dialog.auto_gain_check.setChecked(False)    # Unchecked: keep the best value, do not roll back to 6.0
    assert dialog.gain_box.isEnabled() is True
    assert abs(dialog.gain_box.value() - best) < 0.01   # The spin box shows only two decimals
    assert dialog.gain_box.value() != 6.0
    assert auto_value == 6.0


def test_slider_and_box_stay_in_sync(dialog):
    dialog.auto_gain_check.setChecked(False)
    dialog.gain_slider.setValue(-12.0, emit=True)         # User drags the slider (float, no quantization)
    assert dialog.gain_box.value() == -12.0
    dialog.gain_box.setValue(3.25)             # User edits the spin box (focus loss/arrow keys)
    assert abs(dialog.gain_slider.value() - 3.25) < 1e-6
    assert dialog.gain_db == 3.25


def test_slider_is_continuous(dialog):
    """Mouse position maps directly to dB, no longer limited by QSlider integer steps."""
    dialog.auto_gain_check.setChecked(False)
    dialog.resize(760, 460)
    track = dialog.gain_slider._track_rect()
    mid = track.left() + track.width() * 0.5
    dialog.gain_slider.setValue(dialog.gain_slider._db_at(mid + 0.5))
    assert dialog.gain_slider.value() == dialog.gain_slider._db_at(mid + 0.5)


def test_waveform_follows_gain(dialog):
    dialog.auto_gain_check.setChecked(False)
    dialog.gain_slider.setValue(12.0, emit=True)
    assert abs(dialog.waveform.gain_db - 12.0) < 1e-6
    # Draw the waveform against the 26213 full-scale reference: +12 dB raises the envelope (and may hit the ceiling)
    peak = max(dialog.waveform._peaks)
    assert dialog.waveform._display_peak(peak) > peak
    assert dialog.waveform._display_peak(peak * 100) == 26213.0


def test_processed_samples_carry_the_gain(dialog):
    # Auto mode: peak is raised to the 26213 full-scale reference (APK normalized peak) without clipping
    auto = dialog.processed()
    assert abs(int(np.max(np.abs(auto.astype(np.int32)))) - TONE_AUTO_GAIN_TARGET) <= 1

    # Manual 0 dB: level stays unchanged, proving normalization did not cancel the gain
    dialog.auto_gain_check.setChecked(False)
    dialog.gain_box.setValue(0.0)
    flat = dialog.processed()
    assert int(np.max(np.abs(flat.astype(np.int32)))) == int(
        np.max(np.abs(dialog.selection.astype(np.int32))))


def test_file_name_and_display_name_fields(app):
    """Split the name into file name (.pcm is a fixed suffix) and display name."""
    samples = (np.sin(np.arange(4000) / 30.0) * 3000).astype("<i2")
    dlg = OfbQtToneEditorDialog(None, samples, "demo", "系统-演示样机")
    try:
        assert dlg.file_name == "demo"
        assert dlg.display_name == "系统-演示样机"
        # The suffix stays outside the input; only the body is inside
        assert dlg.file_suffix_label.text() == ".pcm"
        assert ".pcm" not in dlg.file_edit.text()

        dlg.file_edit.setText("  new chime  ")
        dlg.display_edit.setText("  新的铃声  ")
        assert dlg.file_name == "new chime"
        assert dlg.display_name == "新的铃声"
    finally:
        dlg.cleanup()
