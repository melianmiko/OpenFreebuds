"""Custom prompt-tone editor: waveform + two-handle trim + play/pause + loudness gain + Chinese/English naming.
Trim cap 6 s (device PCM limit); output signed 16-bit / 16755 Hz / mono PCM.
Loudness gain: manual slider (-36...+36 dB in 0.1 dB steps) or 'auto gain' to raise the level without clipping.
"""
import os
import tempfile
import wave
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QRect, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from openfreebuds.driver.huawei.prompt_tone import (
    TONE_MAX_DURATION,
    TONE_MAX_SAMPLES,
    TONE_SAMPLE_RATE,
    apply_gain_db,
    peak_gain_db,
)

MIN_SECONDS = 0.2
GAIN_MIN_DB = -36.0
GAIN_MAX_DB = 36.0
TONE_FULL_SCALE = 26213.0   # Full-scale reference: APK normalized peak (0.8 * 32767); waveform limits use the same scale


class ToneWaveform(QWidget):
    """Waveform plus start/end handles; dragging adjusts the trim range, and gain changes redraw at the new level."""

    range_changed = pyqtSignal(int, int)
    HANDLE_GRAB_PX = 12
    ENVELOPE_BINS = 512

    def __init__(self, samples: np.ndarray, parent: QWidget | None = None):
        super().__init__(parent)
        self.samples = samples
        self.total = max(1, samples.size)
        # Precompute the envelope as plain Python data; paintEvent never touches numpy
        self._peaks = self._compute_peaks(samples).tolist()
        self._gain_db = 0.0
        self.start = 0
        self.end = min(self.total, TONE_MAX_SAMPLES)
        self._drag = ""
        self.setMinimumHeight(110)
        self.setMouseTracking(True)

    # --- State -------------------------------------------------------
    def set_gain(self, gain_db: float):
        """When loudness gain changes, redraw the waveform at the new level (the part above full scale is clipped)."""
        gain_db = float(gain_db)
        if gain_db != self._gain_db:
            self._gain_db = gain_db
            self.update()

    @property
    def gain_db(self) -> float:
        return self._gain_db

    def _display_peak(self, peak: float) -> float:
        """Multiply the envelope by gain and clip at full scale; this is the final PCM level."""
        return min(TONE_FULL_SCALE, peak * (10.0 ** (self._gain_db / 20.0)))


    @classmethod
    def _compute_peaks(cls, samples: np.ndarray) -> np.ndarray:
        """Precompute the envelope (512 buckets); paintEvent only looks it up, avoiding numpy slicing during painting."""
        bins = cls.ENVELOPE_BINS
        if samples.size == 0:
            return np.zeros(bins, dtype=np.float64)
        chunk = max(1, samples.size // bins)
        usable = samples[:chunk * bins].astype(np.int32)
        return np.abs(usable.reshape(bins, chunk)).max(axis=1).astype(np.float64)

    # --- State -------------------------------------------------------
    def set_range(self, start: int, end: int):
        min_len = int(MIN_SECONDS * TONE_SAMPLE_RATE)
        max_len = TONE_MAX_SAMPLES
        start = max(0, min(start, self.total - min_len))
        end = max(start + min_len, min(end, self.total, start + max_len))
        if (start, end) != (self.start, self.end):
            self.start, self.end = start, end
            self.update()
            self.range_changed.emit(start, end)

    def _x_of(self, index: int) -> float:
        return self.rect().left() + index / self.total * self.rect().width()

    def _index_of(self, x: float) -> int:
        width = max(1, self.rect().width())
        return int(max(0, min(self.total, (x - self.rect().left()) / width * self.total)))

    # --- Events ------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x = event.position().x()
        if abs(x - self._x_of(self.start)) <= self.HANDLE_GRAB_PX:
            self._drag = "start"
        elif abs(x - self._x_of(self.end)) <= self.HANDLE_GRAB_PX:
            self._drag = "end"
        elif self._x_of(self.start) < x < self._x_of(self.end):
            self._drag = "mid"
            self._drag_offset = self._index_of(x) - self.start
        else:
            index = self._index_of(x)
            span = self.end - self.start
            if index < self.start:
                self.set_range(index, index + span)
            else:
                self.set_range(index - span, index)
            return
        self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        x = event.position().x()
        if self._drag == "start":
            self.set_range(self._index_of(x), self.end)
        elif self._drag == "end":
            self.set_range(self.start, self._index_of(x))
        elif self._drag == "mid":
            span = self.end - self.start
            start = self._index_of(x) - getattr(self, "_drag_offset", span // 2)
            self.set_range(start, start + span)

    def mouseReleaseEvent(self, event):
        self._drag = ""
        self.setCursor(Qt.CursorShape.ArrowCursor)

    # --- Painting ----------------------------------------------------
    def paintEvent(self, event):
        try:
            self._paint(event)
        except Exception:  # Never let paint errors escape into a Qt virtual; PyQt6 aborts the process
            import traceback
            traceback.print_exc()

    def _paint(self, event):
        painter = QPainter(self)
        rect = QRect(self.rect())   # No vertical padding; the waveform fills the widget
        painter.fillRect(self.rect(), QColor("#202028"))

        width = max(1, rect.width())
        peaks = self._peaks
        bins = len(peaks)
        top = rect.top() + rect.height() / 2
        # Draw against the 26213 full-scale reference so gain changes visibly raise or clip the waveform
        scale = (rect.height() / 2) / TONE_FULL_SCALE

        pen_bar = QPen(QColor("#7f86b0"), 1)
        painter.setPen(pen_bar)
        for x in range(width):
            peak = peaks[min(bins - 1, x * bins // width)] if bins else 0.0
            shown = self._display_peak(peak)
            height = min(rect.height() / 2, shown * scale)
            x_pos = rect.left() + x
            painter.drawLine(x_pos, int(top - height), x_pos, int(top + height))

        sel_left = int(self._x_of(self.start))
        sel_right = int(self._x_of(self.end))
        painter.fillRect(QRect(sel_left, rect.top(), max(1, sel_right - sel_left), rect.height()),
                         QColor(255, 204, 102, 40))

        pen_handle = QPen(QColor("#ffcc66"), 2)
        painter.setPen(pen_handle)
        for index in (self.start, self.end):
            x = int(self._x_of(index))
            painter.drawLine(x, rect.top(), x, rect.bottom())
            painter.drawRect(x - 3, int(top) - 4, 6, 8)


class GainSlider(QWidget):
    """Continuous gain slider with 0 centered.
    QSlider stores integers and rounds per pixel, so dragging feels stepped; this maps mouse position to float dB for true continuous dragging, keeping only the center 0 dB tick.
    """

    value_changed = pyqtSignal(float)   # Emitted while dragging to sync the spin box and waveform
    released = pyqtSignal()             # Emitted once on release to apply the value
    HANDLE_RADIUS = 6
    SIDE_MARGIN = 10

    def __init__(self, min_db: float = GAIN_MIN_DB, max_db: float = GAIN_MAX_DB,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._min = float(min_db)
        self._max = float(max_db)
        self._value = 0.0
        self._dragging = False
        self.setMinimumHeight(26)
        self.setMinimumWidth(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # --- Value -------------------------------------------------------
    def value(self) -> float:
        return self._value

    def setValue(self, value: float, emit: bool = False):
        value = max(self._min, min(self._max, float(value)))
        if abs(value - self._value) < 1e-9:
            return
        self._value = value
        self.update()
        if emit:
            self.value_changed.emit(value)

    def _track_rect(self) -> QRect:
        return self.rect().adjusted(self.SIDE_MARGIN, 0, -self.SIDE_MARGIN, 0)

    def _db_at(self, x: float) -> float:
        track = self._track_rect()
        width = max(1, track.width())
        ratio = (x - track.left()) / width
        ratio = max(0.0, min(1.0, ratio))
        return self._min + ratio * (self._max - self._min)

    def _x_of(self, value: float) -> float:
        track = self._track_rect()
        ratio = (value - self._min) / (self._max - self._min) if self._max > self._min else 0.5
        return track.left() + ratio * track.width()

    # --- Events ------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._dragging = True
        self.setValue(self._db_at(event.position().x()), emit=True)

    def mouseMoveEvent(self, event):
        if self._dragging:
            # No quantization: the mouse position maps directly to dB, shown with two decimals
            self.setValue(self._db_at(event.position().x()), emit=True)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.setValue(self._db_at(event.position().x()), emit=True)
            self.released.emit()

    def wheelEvent(self, event):
        step = 0.1 if event.angleDelta().y() > 0 else -0.1
        self.setValue(self._value + step, emit=True)
        self.released.emit()

    def keyPressEvent(self, event):
        step = {Qt.Key.Key_Left: -0.1, Qt.Key.Key_Down: -0.1,
                Qt.Key.Key_Right: 0.1, Qt.Key.Key_Up: 0.1,
                Qt.Key.Key_PageDown: -1.0, Qt.Key.Key_PageUp: 1.0}
        if event.key() in step:
            self.setValue(self._value + step[event.key()], emit=True)
            self.released.emit()
            return
        super().keyPressEvent(event)

    # --- Painting ----------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = self._track_rect()
        mid_y = self.rect().center().y()
        # Use the palette Disabled group so custom-painted controls look disabled
        group = (self.palette().ColorGroup.Active if self.isEnabled()
                 else self.palette().ColorGroup.Disabled)
        palette = self.palette()
        groove = QColor(palette.color(group, palette.ColorRole.Mid))
        groove.setAlpha(160)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(groove)
        painter.drawRoundedRect(QRect(track.left(), mid_y - 2, track.width(), 4), 2, 2)

        # Fill the traversed range with the accent color to show gain direction
        zero_x = int(self._x_of(0.0))
        handle_x = int(self._x_of(self._value))
        accent = QColor(palette.color(group, palette.ColorRole.Highlight))
        if handle_x != zero_x:
            span = QRect(min(zero_x, handle_x), mid_y - 2, abs(handle_x - zero_x), 4)
            painter.setBrush(accent)
            painter.drawRoundedRect(span, 2, 2)

        # Keep only the center 0 dB tick
        tick = QColor(palette.color(group, palette.ColorRole.Text))
        tick.setAlpha(170)
        painter.setPen(QPen(tick, 1))
        painter.drawLine(zero_x, mid_y - 8, zero_x, mid_y + 8)
        painter.drawText(QRect(zero_x - 12, mid_y + 7, 24, 14),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "0")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawEllipse(handle_x - self.HANDLE_RADIUS, mid_y - self.HANDLE_RADIUS,
                            self.HANDLE_RADIUS * 2, self.HANDLE_RADIUS * 2)


class OfbQtToneEditorDialog(QDialog):
    """Trim + naming dialog; on accept it provides samples/start/end and names."""

    def __init__(self, parent: QWidget | None, samples: np.ndarray,
                 file_name: str = "", display_name: str = "", pcm_duration: float | None = None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Custom prompt tone"))
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.samples = np.asarray(samples, dtype="<i2")
        self._tmp_files: list[Path] = []

        self.waveform = ToneWaveform(self.samples, self)

        self.start_box = QDoubleSpinBox(self)
        self.end_box = QDoubleSpinBox(self)
        for box in (self.start_box, self.end_box):
            box.setDecimals(2)
            box.setSingleStep(0.05)
            box.setSuffix(" s")
            box.setMaximum(round(self.samples.size / TONE_SAMPLE_RATE, 2))
        self.start_box.setValue(0.0)
        self.end_box.setValue(min(TONE_MAX_DURATION, round(pcm_duration or self.samples.size / TONE_SAMPLE_RATE, 2)))

        self.duration_label = QLabel(self)
        self.play_button = QPushButton(self.tr("Play"), self)

        # --- Loudness gain -----------------------------------------------
        self.gain_slider = GainSlider(GAIN_MIN_DB, GAIN_MAX_DB, self)
        self.gain_slider.setMinimumWidth(200)

        self.gain_box = QDoubleSpinBox(self)
        self.gain_box.setDecimals(2)
        self.gain_box.setSingleStep(0.1)
        self.gain_box.setRange(GAIN_MIN_DB, GAIN_MAX_DB)
        self.gain_box.setKeyboardTracking(False)   # Apply on focus loss, Enter or arrow keys, not on every keystroke
        self.gain_box.setFixedWidth(84)

        # Keep the unit outside the box so the value matches the x.xx dB layout
        self.gain_unit_label = QLabel("dB", self)

        self.auto_gain_check = QCheckBox(self.tr("Set to the best volume"), self)

        self.gain_hint = QLabel(self)

        gain_row = QHBoxLayout()
        gain_row.addWidget(self.gain_slider, 1)
        gain_row.addWidget(self.gain_box)
        gain_row.addWidget(self.gain_unit_label)
        gain_row.addSpacing(12)
        gain_row.addWidget(self.auto_gain_check)

        # The file name becomes <name>.pcm; the suffix stays outside the input
        self.file_edit = QLineEdit(file_name, self)
        self.file_suffix_label = QLabel(".pcm", self)
        file_row = QHBoxLayout()
        file_row.setContentsMargins(0, 0, 0, 0)
        file_row.addWidget(self.file_edit)
        file_row.addWidget(self.file_suffix_label)

        # Display name is user text and is not localized
        self.display_edit = QLineEdit(display_name, self)

        playback = QHBoxLayout()
        playback.addWidget(self.start_box)
        playback.addWidget(QLabel("→", self))
        playback.addWidget(self.end_box)
        playback.addWidget(self.play_button)
        playback.addWidget(self.duration_label)
        playback.addStretch(1)

        form = QFormLayout()
        form.addRow(self.tr("Start / end"), playback)
        form.addRow(self.tr("Volume"), gain_row)
        form.addRow(self.tr("File Name"), file_row)
        form.addRow(self.tr("Display Name"), self.display_edit)

        hint = QLabel(self.tr("Only the selected range is saved. The 192000-byte limit "
                              "is about 5.7 s at 16755 Hz."), self)
        hint.setWordWrap(True)
        self.gain_hint.setWordWrap(True)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        # Use the application's i18n instead of Qt's qtbase button translations
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("OK"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))

        layout = QVBoxLayout(self)
        layout.addWidget(self.waveform)
        layout.addLayout(form)
        layout.addWidget(self.gain_hint)
        layout.addWidget(hint)
        layout.addWidget(self.buttons)

        self.waveform.range_changed.connect(self._on_range_changed)
        self.start_box.valueChanged.connect(self._on_boxes_changed)
        self.end_box.valueChanged.connect(self._on_boxes_changed)
        self.play_button.clicked.connect(self._on_play)
        self.gain_slider.value_changed.connect(self._on_slider_moved)
        self.gain_slider.released.connect(self._on_gain_applied)
        self.gain_box.valueChanged.connect(self._on_box_gain_changed)
        self.gain_box.editingFinished.connect(self._on_gain_applied)
        self.auto_gain_check.toggled.connect(self._on_auto_toggled)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.auto_gain_check.setChecked(True)   # Default matches the old behavior: normalize the peak without clipping
        self._on_range_changed(self.waveform.start, self.waveform.end)

    # --- Sync --------------------------------------------------------
    def _on_range_changed(self, start: int, end: int):
        for box, value in ((self.start_box, start), (self.end_box, end)):
            box.blockSignals(True)
            box.setValue(round(value / TONE_SAMPLE_RATE, 2))
            box.blockSignals(False)
        self.duration_label.setText(f"{(end - start) / TONE_SAMPLE_RATE:.2f} s")
        if self.auto_gain_check.isChecked():
            self._set_gain_controls(self._auto_gain_value(), from_auto=True)
        self._update_gain_hint()

    def _on_boxes_changed(self):
        start = int(self.start_box.value() * TONE_SAMPLE_RATE)
        end = int(self.end_box.value() * TONE_SAMPLE_RATE)
        self.waveform.set_range(start, end)

    # --- Loudness gain -----------------------------------------------
    @property
    def auto_gain(self) -> bool:
        return self.auto_gain_check.isChecked()

    @property
    def gain_db(self) -> float:
        """Current effective gain: computed from the selection peak in auto mode, or taken from the spin box in manual mode."""
        if self.auto_gain:
            return self._auto_gain_value()
        return float(self.gain_box.value())

    def _auto_gain_value(self) -> float:
        value = peak_gain_db(self.selection)
        return max(GAIN_MIN_DB, min(GAIN_MAX_DB, value))

    def _set_gain_controls(self, value: float, from_auto: bool = False):
        """Write the same value into the slider and the spin box; in from_auto mode keep a 0.01 dB margin in the box."""
        self.gain_slider.setValue(value)
        self.gain_box.blockSignals(True)
        self.gain_box.setValue(round(value if from_auto else self.gain_slider.value(), 2))
        self.gain_box.blockSignals(False)
        self.waveform.set_gain(self.gain_slider.value())

    def _on_slider_moved(self, value: float):
        """While dragging: the spin box follows and the waveform redraws live; the preview file is rewritten only on release."""
        self.gain_box.blockSignals(True)
        self.gain_box.setValue(round(value, 2))
        self.gain_box.blockSignals(False)
        self.waveform.set_gain(value)
        self._update_gain_hint()

    def _on_box_gain_changed(self, value: float):
        self.gain_slider.setValue(value)
        self._on_gain_applied()   # Arrow-key changes apply immediately without waiting for focus loss

    def _on_auto_toggled(self, checked: bool):
        if checked:
            # Checked: compute and write back the best gain, updating slider, box and waveform
            self._set_gain_controls(self._auto_gain_value(), from_auto=True)
        self.gain_slider.setEnabled(not checked)
        self.gain_box.setEnabled(not checked)
        self.gain_slider.update()   # Force a repaint after disabling so the state change is visible
        self.gain_box.update()
        # Unchecking keeps the current best value instead of restoring the old one
        self._update_gain_hint()
        self.waveform.set_gain(self.gain_db)
        self._restart_preview_if_playing()

    def _on_gain_applied(self):
        """Gesture end/focus loss/arrow keys: apply immediately, rewrite the preview audio, and replay at the new level if playing."""
        if self.auto_gain:
            self._set_gain_controls(self._auto_gain_value(), from_auto=True)
        self.waveform.set_gain(self.gain_db)
        self._update_gain_hint()
        self._restart_preview_if_playing()

    def _update_gain_hint(self):
        gain = self.gain_db
        chunk = self.selection.astype(np.int32)
        peak = int(np.max(np.abs(chunk))) if chunk.size else 0
        if self.auto_gain:
            # In auto mode, show the measured and target peaks so the result is clear
            applied = int(round(peak * (10.0 ** (gain / 20.0)))) if peak else 0
            # Use a neutral 'change to' wording for both positive and negative gain
            self.gain_hint.setText(self.tr("Best gain {0} dB — peak {1} changed to {2}.")
                                   .format(f"{gain:+.2f}", peak, applied))
            self.gain_hint.setStyleSheet("color: palette(mid);")
            return
        # Warn only when manual gain pushes the peak strictly above 26213
        over = peak > 0 and round(peak * (10.0 ** (gain / 20.0))) > TONE_FULL_SCALE
        if over:
            self.gain_hint.setText(self.tr("Exceeds full loudness, the signal may clip."))
            self.gain_hint.setStyleSheet("color: #d9534f;")
        else:
            self.gain_hint.clear()
            self.gain_hint.setStyleSheet("")

    # --- Playback ----------------------------------------------------
    def processed(self, samples: np.ndarray | None = None) -> np.ndarray:
        """Samples processed with the current gain, ready to save/preview (auto mode equals peak normalization)."""
        chunk = self.selection if samples is None else samples
        return apply_gain_db(chunk, self.gain_db)

    def _selection_wav(self) -> Path:
        chunk = self.processed()
        # QMediaPlayer on Windows can cut off short WAV files early;
        # append 120 ms of silence so no audio frame is lost.
        tail = np.zeros(int(TONE_SAMPLE_RATE * 0.12), dtype=chunk.dtype)
        fd, tmp_name = tempfile.mkstemp(suffix=".wav", prefix="ofb_preview_")
        os.close(fd)
        fd_path = Path(tmp_name)
        self._tmp_files.append(fd_path)
        with wave.open(str(fd_path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(TONE_SAMPLE_RATE)
            w.writeframes(np.concatenate([chunk, tail]).tobytes())
        return fd_path

    def _restart_preview_if_playing(self):
        """Gain changed while playing: replay at the new level so what is heard matches what will be saved."""
        player = getattr(self, "_player", None)
        if player is None:
            return
        from PyQt6.QtMultimedia import QMediaPlayer
        if player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return
        player.stop()
        player.setSource(QUrl())
        self._discard_previews()
        player.setSource(QUrl.fromLocalFile(str(self._selection_wav())))
        player.play()

    def _on_play(self):
        try:
            from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
        except ImportError:
            self.play_button.setEnabled(False)
            return
        if not hasattr(self, "_player"):
            self._player = QMediaPlayer(self)
            self._output = QAudioOutput(self)
            self._player.setAudioOutput(self._output)
            self._player.playbackStateChanged.connect(self._on_state)
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.stop()
            return
        # Release the previous preview file first; the Windows media backend locks it
        self._player.stop()
        self._player.setSource(QUrl())
        self._discard_previews()
        self._player.setSource(QUrl.fromLocalFile(str(self._selection_wav())))
        self._player.play()

    def _discard_previews(self):
        """Delete the temporary preview file no longer referenced by the player; if deletion fails, leave it to the system temp directory."""
        for path in self._tmp_files:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        self._tmp_files.clear()

    def _on_state(self, state):
        self.play_button.setText(
            self.tr("Pause") if state == self._player.PlaybackState.PlayingState else self.tr("Play"))

    # --- Result ------------------------------------------------------
    def done(self, result: int):
        # Every close path (OK, Cancel, Esc, title-bar close) goes through done();
        # stop the preview before the dialog disappears so audio never outlives it.
        self.cleanup()
        super().done(result)

    def cleanup(self):
        if hasattr(self, "_player"):
            self._player.stop()
            self._player.setSource(QUrl())   # Release the file handle, otherwise unlink fails with WinError 32
        self._discard_previews()

    @property
    def selection(self) -> np.ndarray:
        return self.samples[self.waveform.start:self.waveform.end]

    @property
    def file_name(self) -> str:
        """File name body (without .pcm)."""
        return self.file_edit.text().strip()

    @property
    def display_name(self) -> str:
        return self.display_edit.text().strip()
