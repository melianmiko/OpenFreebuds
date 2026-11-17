"""Offscreen tests for the loudness-gain control: sync, disabling, no rollback, and gain actually applied to samples."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PyQt6")
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication, QSizePolicy

from openfreebuds.driver.huawei.prompt_tone import TONE_AUTO_GAIN_TARGET, TONE_MAX_SAMPLES, TONE_SAMPLE_RATE
from openfreebuds_qt.app.dialog.tone_editor import OfbQtToneEditorDialog, ToneWaveform


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


def test_long_source_keeps_full_waveform_and_allows_late_selection(app):
    """Importing a long file must not truncate it before the editor: later time ranges stay selectable."""
    samples = np.zeros(TONE_MAX_SAMPLES * 3, dtype="<i2")
    dlg = OfbQtToneEditorDialog(None, samples)
    try:
        assert dlg.samples.size == samples.size
        assert dlg.waveform.total == samples.size
        assert dlg.end_box.maximum() > TONE_MAX_SAMPLES / TONE_SAMPLE_RATE

        # Select a window that starts two max-length segments into the source
        start = TONE_MAX_SAMPLES * 2
        dlg.waveform.set_range(start, samples.size)
        assert dlg.waveform.start == start
        assert dlg.selection.size == TONE_MAX_SAMPLES
    finally:
        dlg.cleanup()


def test_selection_has_no_minimum_length(dialog):
    """The waveform allows zero and one-sample selections; only the PCM cap remains."""
    dialog.waveform.set_range(1000, 1000)
    assert dialog.waveform.start == 1000
    assert dialog.waveform.end == 1000
    assert dialog.selection.size == 0

    dialog.waveform.set_range(1000, 1001)
    assert dialog.waveform.end - dialog.waveform.start == 1
    assert dialog.selection.size == 1


def test_end_handle_crosses_start_and_keeps_dragging(app):
    """Dragging the back handle before the front swaps roles without ending the drag."""
    waveform = ToneWaveform(np.zeros(10000, dtype="<i2"))
    waveform.set_range(2000, 5000)
    waveform._drag = "end"

    waveform._move_handle(1000)
    assert (waveform.start, waveform.end) == (1000, 2000)
    assert waveform._drag == "start"

    waveform._move_handle(500)
    assert (waveform.start, waveform.end) == (500, 2000)
    assert waveform._drag == "start"


def test_start_handle_crosses_end_and_keeps_dragging(app):
    """The symmetric case: dragging the front handle past the back swaps to end."""
    waveform = ToneWaveform(np.zeros(10000, dtype="<i2"))
    waveform.set_range(2000, 5000)
    waveform._drag = "start"

    waveform._move_handle(6000)
    assert (waveform.start, waveform.end) == (5000, 6000)
    assert waveform._drag == "end"

    waveform._move_handle(7000)
    assert (waveform.start, waveform.end) == (5000, 7000)
    assert waveform._drag == "end"


def test_overlapping_handles_choose_role_from_drag_direction(app):
    """At an exact overlap, leftward drag moves the front handle and rightward moves the back handle."""
    waveform = ToneWaveform(np.zeros(10000, dtype="<i2"))
    waveform.set_range(2000, 2000)

    waveform._drag = "start"
    waveform._move_handle(1500)
    assert (waveform.start, waveform.end) == (1500, 2000)
    assert waveform._drag == "start"

    waveform.set_range(2000, 2000)
    waveform._drag = "start"
    waveform._move_handle(2500)
    assert (waveform.start, waveform.end) == (2000, 2500)
    assert waveform._drag == "end"


def test_range_cap_keeps_the_dragged_handle_under_the_pointer(app):
    """When the selection reaches the PCM cap, the active handle is the one that stops."""
    total = TONE_MAX_SAMPLES * 3
    waveform = ToneWaveform(np.zeros(total, dtype="<i2"))
    waveform.set_range(TONE_MAX_SAMPLES, total, active="end")
    assert waveform.end - waveform.start == TONE_MAX_SAMPLES
    assert waveform.start == TONE_MAX_SAMPLES

    waveform.set_range(TONE_MAX_SAMPLES, total, active="start")
    assert waveform.end - waveform.start == TONE_MAX_SAMPLES
    assert waveform.end == total


def test_clamped_box_values_snap_back_to_waveform(app):
    """A typed value outside the allowed window must not stay ahead of the actual handles."""
    dlg = OfbQtToneEditorDialog(None, np.zeros(100000, dtype="<i2"))
    try:
        # No minimum: a 0.03 s selection is accepted instead of being forced to 0.2 s.
        dlg.start_box.setValue(5.77)
        dlg.start_box.editingFinished.emit()
        dlg.end_box.setValue(5.80)
        dlg.end_box.editingFinished.emit()
        assert abs(dlg.waveform.end / TONE_SAMPLE_RATE - 5.80) < 0.006
        assert dlg.waveform.end - dlg.waveform.start < 0.1 * TONE_SAMPLE_RATE

        # The end handle can still use the remaining source, and the box follows it.
        dlg.end_box.setValue(5.90)
        dlg.end_box.editingFinished.emit()
        assert abs(dlg.end_box.value() - dlg.waveform.end / TONE_SAMPLE_RATE) < 0.006
    finally:
        dlg.cleanup()


def test_done_stops_preview_audio(app):
    """OK, Cancel, Esc and the title-bar close all must stop the editor preview."""
    calls = []

    class _FakePlayer:
        def stop(self):
            calls.append("stop")

        def setSource(self, _source):
            calls.append("clear")

    dlg = OfbQtToneEditorDialog(None, np.zeros(8000, dtype="<i2"))
    dlg._player = _FakePlayer()
    dlg.done(0)

    assert calls[:2] == ["stop", "clear"]


def test_end_handle_snaps_at_cap_then_slides_window(app):
    """Reaching the PCM cap sticks to it; continuing right drags the start handle along."""
    waveform = ToneWaveform(np.zeros(TONE_MAX_SAMPLES * 3, dtype="<i2"))
    waveform.resize(800, 200)
    waveform.set_range(0, TONE_MAX_SAMPLES)
    waveform._drag = "end"

    waveform._move_handle(TONE_MAX_SAMPLES + 100)      # Inside the magnetic zone
    assert (waveform.start, waveform.end) == (0, TONE_MAX_SAMPLES)

    waveform._move_handle(TONE_MAX_SAMPLES + 5000)     # Beyond it: the window slides
    assert waveform.end - waveform.start == TONE_MAX_SAMPLES
    assert waveform.start == 5000


def test_start_handle_snaps_at_cap_then_slides_window(app):
    """Mirror case: dragging the start handle left at the cap drags the end handle along."""
    total = TONE_MAX_SAMPLES * 3
    waveform = ToneWaveform(np.zeros(total, dtype="<i2"))
    waveform.resize(800, 200)
    waveform.set_range(total - TONE_MAX_SAMPLES, total)
    waveform._drag = "start"

    waveform._move_handle(total - TONE_MAX_SAMPLES - 100)
    assert (waveform.start, waveform.end) == (total - TONE_MAX_SAMPLES, total)

    waveform._move_handle(total - TONE_MAX_SAMPLES - 5000)
    assert waveform.end - waveform.start == TONE_MAX_SAMPLES
    assert waveform.end == total - 5000


def test_time_box_commits_on_finish_only(app):
    """Typing a time must not touch the waveform until focus loss or Enter."""
    dlg = OfbQtToneEditorDialog(None, np.zeros(100000, dtype="<i2"))
    try:
        start_before = dlg.waveform.start
        dlg.start_box.setValue(1.0)
        assert dlg.waveform.start == start_before
        dlg.start_box.editingFinished.emit()
        assert abs(dlg.waveform.start / TONE_SAMPLE_RATE - 1.0) < 0.006
    finally:
        dlg.cleanup()


def test_start_box_pulls_end_handle_when_too_far(app):
    """The typed start wins; a distant end handle is pulled to start + 0.5 s."""
    rate = TONE_SAMPLE_RATE
    dlg = OfbQtToneEditorDialog(None, np.zeros(int(110 * rate), dtype="<i2"))
    try:
        dlg.waveform.set_range(int(25 * rate), int(25 * rate))
        dlg.start_box.setValue(100.0)
        dlg.start_box.editingFinished.emit()
        assert abs(dlg.waveform.start / rate - 100.0) < 0.006
        assert abs(dlg.waveform.end / rate - 100.5) < 0.012

        dlg.waveform.set_range(int(108 * rate), int(108 * rate))
        dlg.start_box.setValue(100.0)
        dlg.start_box.editingFinished.emit()
        assert abs(dlg.waveform.end / rate - 100.5) < 0.012
    finally:
        dlg.cleanup()


def test_end_box_pulls_start_handle_when_too_far(app):
    """The typed end wins; a distant start handle is pulled to end - 0.5 s."""
    rate = TONE_SAMPLE_RATE
    dlg = OfbQtToneEditorDialog(None, np.zeros(int(110 * rate), dtype="<i2"))
    try:
        dlg.waveform.set_range(0, 0)
        dlg.end_box.setValue(100.0)
        dlg.end_box.editingFinished.emit()
        assert abs(dlg.waveform.end / rate - 100.0) < 0.006
        assert abs(dlg.waveform.start / rate - 99.5) < 0.012
    finally:
        dlg.cleanup()


def test_time_boxes_swap_when_order_is_inverted(app):
    """A legal distance in the wrong order is corrected by swapping the handles."""
    rate = TONE_SAMPLE_RATE
    dlg = OfbQtToneEditorDialog(None, np.zeros(int(110 * rate), dtype="<i2"))
    try:
        dlg.waveform.set_range(int(98 * rate), int(99 * rate))
        dlg.start_box.setValue(100.0)
        dlg.start_box.editingFinished.emit()
        assert abs(dlg.waveform.start / rate - 99.0) < 0.012
        assert abs(dlg.waveform.end / rate - 100.0) < 0.012
    finally:
        dlg.cleanup()


def test_time_box_keeps_input_when_other_handle_hits_the_audio_end(app):
    """Near the source end the typed value is kept and the other handle clamps to the end."""
    rate = TONE_SAMPLE_RATE
    total = int(110 * rate)
    dlg = OfbQtToneEditorDialog(None, np.zeros(total, dtype="<i2"))
    try:
        dlg.waveform.set_range(0, 0)
        dlg.start_box.setValue(109.8)
        dlg.start_box.editingFinished.emit()
        assert abs(dlg.waveform.start / rate - 109.8) < 0.012
        assert dlg.waveform.end == total
    finally:
        dlg.cleanup()


def test_zoom_never_below_full_track(app):
    """100% is the floor: the whole track stays visible and cannot be zoomed out."""
    waveform = ToneWaveform(np.zeros(100000, dtype="<i2"))
    waveform.resize(800, 200)
    waveform.set_zoom(0.5)
    assert waveform.zoom == 1.0
    assert (waveform.view_start, waveform.view_span) == (0, 100000)


def test_zoom_keeps_the_sample_under_the_cursor(app):
    """Zooming is anchored: the sample below the cursor stays at the same x."""
    waveform = ToneWaveform(np.zeros(100000, dtype="<i2"))
    waveform.resize(800, 200)
    anchor_index = waveform._index_of(200)
    waveform.set_zoom(10.0, anchor_x=200)
    assert abs(waveform._index_of(200) - anchor_index) <= 2


def test_max_zoom_is_sample_level(app):
    """At the maximum zoom one sample still occupies at least four pixels."""
    waveform = ToneWaveform(np.zeros(100000, dtype="<i2"))
    waveform.resize(800, 200)
    waveform.set_zoom(waveform.max_zoom)
    assert waveform.view_span * 4 >= waveform.width()
    assert waveform.view_span * 4 <= waveform.width() + 4


def test_resize_reclamps_zoom(app):
    """A wider window lowers the maximum zoom, so the current zoom is released."""
    waveform = ToneWaveform(np.zeros(100000, dtype="<i2"))
    waveform.show()
    waveform.resize(400, 200)
    waveform.set_zoom(waveform.max_zoom)
    assert waveform.view_span == 100
    waveform.resize(800, 200)
    app.processEvents()   # Hidden widgets do not receive resize events; a shown one does
    assert waveform.view_span == 200


def test_plain_wheel_pans_and_ctrl_wheel_zooms(app):
    """Plain wheel moves the view horizontally; Ctrl+wheel zooms."""
    waveform = ToneWaveform(np.zeros(100000, dtype="<i2"))
    waveform.resize(800, 200)
    waveform.set_zoom(4.0)
    start_before = waveform.view_start
    event = QWheelEvent(QPointF(400, 50), QPointF(400, 50), QPoint(0, 0), QPoint(0, -120),
                        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                        Qt.ScrollPhase.NoScrollPhase, False)
    waveform.wheelEvent(event)
    assert waveform.view_start == start_before + max(1, int(waveform.view_span * 0.1))

    zoom_before = waveform.zoom
    ctrl_event = QWheelEvent(QPointF(400, 50), QPointF(400, 50), QPoint(0, 0), QPoint(0, 120),
                             Qt.MouseButton.NoButton, Qt.KeyboardModifier.ControlModifier,
                             Qt.ScrollPhase.NoScrollPhase, False)
    waveform.wheelEvent(ctrl_event)
    assert waveform.zoom > zoom_before


def test_zoom_label_switches_to_multiplier_at_100x(app):
    """Below 10000% the readout stays a percentage; 100x and above use a multiplier."""
    dlg = OfbQtToneEditorDialog(None, np.zeros(100000, dtype="<i2"))
    try:
        dlg.show()
        dlg.resize(900, 600)
        dlg.waveform.set_zoom(99.0)
        app.processEvents()
        assert dlg.zoom_label.text().endswith("%")
        assert dlg.zoom_label.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Fixed
        percent_width = dlg.zoom_label.width()
        dlg.waveform.set_zoom(100.0)
        app.processEvents()
        assert dlg.zoom_label.text() == "100.00x"
        assert dlg.zoom_label.width() > percent_width
    finally:
        dlg.cleanup()


def test_layout_only_waveform_absorbs_extra_height(app):
    """Window height goes to the waveform; hint labels keep their natural height."""
    dlg = OfbQtToneEditorDialog(None, np.zeros(40000, dtype="<i2"))
    try:
        assert dlg.layout().stretch(1) == 1
        assert dlg.waveform.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Expanding
        assert dlg.gain_hint.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Minimum
        assert dlg.start_box.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
        assert dlg.end_box.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
    finally:
        dlg.cleanup()


def test_overview_drag_moves_the_view_without_touching_the_selection(app):
    """Clicking/dragging the overview pans; the trim range stays unchanged."""
    dlg = OfbQtToneEditorDialog(None, np.zeros(100000, dtype="<i2"))
    try:
        dlg.waveform.resize(800, 200)
        dlg.overview.resize(800, 44)
        dlg.waveform.set_zoom(4.0)
        selection = (dlg.waveform.start, dlg.waveform.end)
        before = dlg.waveform.view_start
        dlg.overview._center_view(600)
        assert dlg.waveform.view_start != before
        assert (dlg.waveform.start, dlg.waveform.end) == selection
    finally:
        dlg.cleanup()