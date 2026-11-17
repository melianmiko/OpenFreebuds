"""Custom prompt-tone editor: waveform + two-handle trim + play/pause + loudness gain + Chinese/English naming.
Selection has no minimum length; the saved PCM still caps at 6 s (device limit). Output signed 16-bit / 16755 Hz / mono PCM.
Loudness gain: manual slider (-36...+36 dB in 0.1 dB steps) or 'auto gain' to raise the level without clipping.
"""
import math
import os
import tempfile
import wave
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QRect, QSize, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPalette, QPen, QPixmap
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
    QSizePolicy,
    QSlider,
    QToolButton,
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

GAIN_MIN_DB = -36.0
GAIN_MAX_DB = 36.0
TONE_FULL_SCALE = 26213.0   # Full-scale reference: APK normalized peak (0.8 * 32767); waveform limits use the same scale


class ToneWaveform(QWidget):
    """Zoomable waveform with two trim handles.

    The visible window is (view_start, view_span). Ctrl+wheel zooms at the
    cursor, the plain wheel pans horizontally, and reaching the PCM cap first
    snaps and then slides the whole selection so the dragged handle keeps
    following the pointer.
    """

    range_changed = pyqtSignal(int, int)
    view_changed = pyqtSignal(int, int)   # Visible start and span, in samples

    HANDLE_GRAB_PX = 12
    ENVELOPE_BINS = 512
    BLOCK_SIZE = 32
    SNAP_PX = 4
    ZOOM_STEP = 1.25
    MIN_SAMPLES_PER_PX = 0.25   # At max zoom one sample is at least 4 px wide
    EDGE_PAN_PX = 8

    def __init__(self, samples: np.ndarray, parent: QWidget | None = None):
        super().__init__(parent)
        self.samples = samples
        self.total = max(1, samples.size)
        # Precompute the envelope as plain Python data; paintEvent never touches numpy
        self._peaks = self._compute_peaks(samples).tolist()
        self._block_peaks = self._compute_block_peaks(samples)
        self._gain_db = 0.0
        self.start = 0
        self.end = min(self.total, TONE_MAX_SAMPLES)
        self._drag = ""
        self._drag_offset = 0
        self._view_start = 0
        self._view_span = self.total
        self._cache_key = None
        self._cache_peaks = None
        self.setMinimumHeight(110)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
        """Precompute the coarse envelope (512 buckets); used by the zoomed-out overview."""
        bins = cls.ENVELOPE_BINS
        if samples.size == 0:
            return np.zeros(bins, dtype=np.float64)
        chunk = max(1, samples.size // bins)
        usable = samples[:chunk * bins].astype(np.int32)
        return np.abs(usable.reshape(bins, chunk)).max(axis=1).astype(np.float64)

    @classmethod
    def _compute_block_peaks(cls, samples: np.ndarray) -> np.ndarray:
        """Max-abs value per fixed block, used to build the per-pixel envelope quickly."""
        block = cls.BLOCK_SIZE
        if samples.size == 0:
            return np.zeros(1, dtype=np.float64)
        count = (samples.size + block - 1) // block
        buffer = np.zeros(count * block, dtype=np.int32)
        buffer[:samples.size] = np.abs(samples.astype(np.int32))
        return buffer.reshape(count, block).max(axis=1).astype(np.float64)

    # --- View --------------------------------------------------------
    @property
    def view_start(self) -> int:
        return self._view_start

    @property
    def view_span(self) -> int:
        return self._view_span

    @property
    def zoom(self) -> float:
        """1.0 shows the whole track; larger values magnify it."""
        return self.total / max(1, self._view_span)

    def min_view_span(self) -> int:
        """Smallest visible span: at that zoom one sample still covers four pixels."""
        return max(1, int(round(self.width() * self.MIN_SAMPLES_PER_PX)))

    @property
    def max_zoom(self) -> float:
        return max(1.0, self.total / self.min_view_span())

    def set_view(self, start: int, span: int, emit: bool = True) -> bool:
        """Clamp and apply the visible window; returns True when it actually changed."""
        span = int(max(self.min_view_span(), min(self.total, span)))
        start = int(max(0, min(start, self.total - span)))
        if (start, span) == (self._view_start, self._view_span):
            return False
        self._view_start, self._view_span = start, span
        self._cache_key = None
        self.update()
        if emit:
            self.view_changed.emit(start, span)
        return True

    def set_zoom(self, zoom: float, anchor_x: float | None = None) -> bool:
        """Zoom around a widget x coordinate (default: center) and keep that point fixed."""
        zoom = max(1.0, min(self.max_zoom, float(zoom)))
        span = int(max(self.min_view_span(), min(self.total, round(self.total / zoom))))
        if anchor_x is None:
            anchor_x = self.width() / 2.0
        width = max(1, self.rect().width())
        ratio = max(0.0, min(1.0, (anchor_x - self.rect().left()) / width))
        anchor_index = self._view_start + ratio * self._view_span
        start = int(round(anchor_index - ratio * span))
        return self.set_view(start, span)

    def reset_view(self):
        self.set_view(0, self.total)

    def pan_by(self, samples_delta: int) -> bool:
        return self.set_view(self._view_start + samples_delta, self._view_span)

    def center_on(self, index: int):
        """Center the view on a sample index, keeping the current zoom."""
        self.set_view(int(index) - self._view_span // 2, self._view_span)

    def _snap_samples(self) -> int:
        """Width of the magnetic zone around the PCM cap, in samples."""
        return max(1, int(self.SNAP_PX * self._view_span / max(1, self.width())))

    def _view_peaks(self, width: int) -> np.ndarray:
        """Per-pixel max-abs values for the visible window, cached per view and width."""
        key = (self._view_start, self._view_span, width)
        if key == self._cache_key and self._cache_peaks is not None:
            return self._cache_peaks
        span = max(1, self._view_span)
        start = max(0, min(self._view_start, max(0, self.total - span)))
        offsets = (np.arange(width + 1, dtype=np.int64) * span) // width
        if span <= width * self.BLOCK_SIZE:
            segment = np.abs(self.samples[start:start + span].astype(np.int32))
            if segment.size == 0:
                peaks = np.zeros(width, dtype=np.float64)
            else:
                starts = np.clip(offsets[:-1], 0, segment.size - 1)
                peaks = np.maximum.reduceat(segment, starts).astype(np.float64)
        else:
            blocks = self._block_peaks
            starts = np.clip((start + offsets[:-1]) // self.BLOCK_SIZE, 0, blocks.size - 1)
            peaks = np.maximum.reduceat(blocks, starts)
        self._cache_key = key
        self._cache_peaks = peaks
        return peaks

    # --- State -------------------------------------------------------
    def set_range(self, start: int, end: int, active: str | None = None):
        """Clamp a range to the source and the PCM cap without enforcing a minimum length.

        active tells which handle the user is dragging, so when the cap is reached the
        handle under the pointer stops instead of the other one moving unexpectedly.
        """
        start = max(0, min(start, self.total))
        end = max(0, min(end, self.total))
        if start > end:
            # A text-box edit cannot invert the range; collapse it at the other handle.
            start = end
        if end - start > TONE_MAX_SAMPLES:
            if active == "start":
                start = end - TONE_MAX_SAMPLES
            else:
                end = start + TONE_MAX_SAMPLES
        if (start, end) != (self.start, self.end):
            self.start, self.end = start, end
            self.update()
            self.range_changed.emit(start, end)

    def _x_of(self, index: int) -> float:
        left = self.rect().left()
        return left + (index - self._view_start) / max(1, self._view_span) * self.rect().width()

    def _index_of(self, x: float) -> int:
        width = max(1, self.rect().width())
        index = self._view_start + (x - self.rect().left()) / width * self._view_span
        return int(max(0, min(self.total, round(index))))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        span = max(self.min_view_span(), min(self.total, self._view_span))
        start = int(max(0, min(self._view_start, self.total - span)))
        if not self.set_view(start, span, emit=False):
            self._cache_key = None   # The widget width changed; per-pixel peaks must be rebuilt
            self.view_changed.emit(self._view_start, self._view_span)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta:
                self.set_zoom(self.zoom * (self.ZOOM_STEP ** (delta / 120.0)),
                              anchor_x=event.position().x())
                event.accept()
                return
        # Plain wheel: horizontal panning (trackpads report horizontal deltas too)
        delta = event.angleDelta().y() + event.angleDelta().x()
        if delta:
            step = max(1, int(self._view_span * 0.1))
            self.pan_by(step if delta < 0 else -step)
            event.accept()
            return
        super().wheelEvent(event)


    # --- Events ------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x = event.position().x()
        start_dist = abs(x - self._x_of(self.start))
        end_dist = abs(x - self._x_of(self.end))
        start_hit = start_dist <= self.HANDLE_GRAB_PX
        end_hit = end_dist <= self.HANDLE_GRAB_PX
        if start_hit and end_hit:
            # Overlapping handles: whichever is nearer keeps the press; on an exact
            # overlap start wins, then the first move decides the direction (see _move_handle).
            self._drag = "start" if start_dist <= end_dist else "end"
        elif start_hit:
            self._drag = "start"
        elif end_hit:
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

    def _move_handle(self, index: int):
        """Move the active handle; at the PCM cap the window slides, and crossing swaps roles.

        Reaching the cap first sticks to the exact limit (magnetic zone around it),
        then continuing in the same direction moves the other handle so the
        dragged one can keep following the pointer.
        """
        snap = self._snap_samples()
        if self._drag == "start":
            if index > self.end:
                self._drag = "end"
                self.set_range(self.end, index, active="end")
                return
            cap = self.end - TONE_MAX_SAMPLES
            if index < cap - snap:
                new_start = max(0, index)
                self.set_range(new_start, min(self.total, new_start + TONE_MAX_SAMPLES), active="start")
            elif index <= cap + snap:
                self.set_range(max(0, cap), self.end, active="start")
            else:
                self.set_range(index, self.end, active="start")
        elif self._drag == "end":
            if index < self.start:
                self._drag = "start"
                self.set_range(index, self.start, active="start")
                return
            cap = self.start + TONE_MAX_SAMPLES
            if index > cap + snap:
                new_end = min(self.total, index)
                self.set_range(max(0, new_end - TONE_MAX_SAMPLES), new_end, active="end")
            elif index >= cap - snap:
                self.set_range(self.start, min(self.total, cap), active="end")
            else:
                self.set_range(self.start, index, active="end")

    def mouseMoveEvent(self, event):
        x = event.position().x()
        if self._drag in ("start", "end"):
            # At a zoomed view the pointer would leave the visible range; pan so the
            # drag can continue instead of stopping at the widget edge.
            step = max(1, int(self._view_span * 0.05))
            if x < self.EDGE_PAN_PX and self._view_start > 0:
                self.pan_by(-step)
            elif x > self.width() - self.EDGE_PAN_PX and self._view_start + self._view_span < self.total:
                self.pan_by(step)
            self._move_handle(self._index_of(x))
        elif self._drag == "mid":
            span = self.end - self.start
            start = self._index_of(x) - self._drag_offset
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
        peaks = self._view_peaks(width)
        top = rect.top() + rect.height() / 2
        # Draw against the 26213 full-scale reference so gain changes visibly raise or clip the waveform
        scale = (rect.height() / 2) / TONE_FULL_SCALE

        pen_bar = QPen(QColor("#7f86b0"), 1)
        painter.setPen(pen_bar)
        for x in range(width):
            peak = float(peaks[x]) if x < len(peaks) else 0.0
            shown = self._display_peak(peak)
            height = min(rect.height() / 2, shown * scale)
            x_pos = rect.left() + x
            painter.drawLine(x_pos, int(top - height), x_pos, int(top + height))

        # Once a pixel covers less than one sample, draw the real sample polyline
        if self._view_span <= width:
            gain = 10.0 ** (self._gain_db / 20.0)
            first = max(0, self._view_start)
            last = min(self.total, self._view_start + self._view_span)
            if last - first <= width * 4:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                painter.setPen(QPen(QColor("#aab1e0"), 1))
                path = QPainterPath()
                for index in range(first, last):
                    value = max(-TONE_FULL_SCALE, min(TONE_FULL_SCALE, float(self.samples[index]) * gain))
                    x_pos = self._x_of(index)
                    y_pos = top - value * scale
                    if index == first:
                        path.moveTo(x_pos, y_pos)
                    else:
                        path.lineTo(x_pos, y_pos)
                painter.drawPath(path)

        sel_left = max(rect.left(), min(rect.right(), int(self._x_of(self.start))))
        sel_right = max(rect.left(), min(rect.right(), int(self._x_of(self.end))))
        if sel_right > rect.left() and sel_left < rect.right():
            painter.fillRect(QRect(sel_left, rect.top(), max(1, sel_right - sel_left), rect.height()),
                             QColor(255, 204, 102, 40))

        pen_handle = QPen(QColor("#ffcc66"), 2)
        painter.setPen(pen_handle)
        for index in (self.start, self.end):
            x = int(self._x_of(index))
            if rect.left() - 2 <= x <= rect.right() + 2:
                painter.drawLine(x, rect.top(), x, rect.bottom())
                painter.drawRect(x - 3, int(top) - 4, 6, 8)


class ToneOverview(QWidget):
    """Whole-track miniature showing the selection, the visible viewport and both handles.

    Click or drag to move the viewport; the zoom level is kept.
    """

    def __init__(self, samples: np.ndarray, parent: QWidget | None = None):
        super().__init__(parent)
        self.total = max(1, samples.size)
        self._peaks = ToneWaveform._compute_peaks(samples).tolist()
        self.waveform: ToneWaveform | None = None
        self._dragging = False
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def bind(self, waveform: ToneWaveform):
        self.waveform = waveform
        waveform.view_changed.connect(self._on_view_changed)
        waveform.range_changed.connect(self._on_view_changed)

    def _on_view_changed(self, *_args):
        self.update()

    def _x_of(self, index: int) -> float:
        left = self.rect().left()
        return left + index / self.total * self.rect().width()

    def _index_at(self, x: float) -> int:
        width = max(1, self.rect().width())
        return int(max(0, min(self.total, (x - self.rect().left()) / width * self.total)))

    def _center_view(self, x: float):
        if self.waveform is not None:
            self.waveform.center_on(self._index_at(x))

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.waveform is None:
            return
        self._dragging = True
        self._center_view(event.position().x())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._center_view(event.position().x())

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def paintEvent(self, event):
        try:
            self._paint()
        except Exception:  # Never let paint errors escape into a Qt virtual; PyQt6 aborts the process
            import traceback
            traceback.print_exc()

    def _paint(self):
        painter = QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, QColor("#26262f"))

        width = max(1, rect.width())
        peaks = self._peaks
        bins = len(peaks)
        top = rect.top() + rect.height() / 2
        scale = (rect.height() / 2) / TONE_FULL_SCALE

        painter.setPen(QPen(QColor("#6f769e"), 1))
        for x in range(width):
            peak = peaks[min(bins - 1, x * bins // width)] if bins else 0.0
            height = min(rect.height() / 2, min(TONE_FULL_SCALE, peak) * scale)
            painter.drawLine(rect.left() + x, int(top - height), rect.left() + x, int(top + height))

        if self.waveform is None:
            return
        # Selection
        sel_left = int(self._x_of(self.waveform.start))
        sel_right = int(self._x_of(self.waveform.end))
        painter.fillRect(QRect(sel_left, rect.top(), max(1, sel_right - sel_left), rect.height()),
                         QColor(255, 204, 102, 46))

        # Visible viewport
        view_left = int(self._x_of(self.waveform.view_start))
        view_right = int(self._x_of(self.waveform.view_start + self.waveform.view_span))
        view = QRect(view_left, rect.top(), max(2, view_right - view_left), rect.height() - 1)
        painter.fillRect(view, QColor(255, 255, 255, 18))
        painter.setPen(QPen(QColor("#b8c0ff"), 1))
        painter.drawRect(view)

        # Handles
        painter.setPen(QPen(QColor("#ffcc66"), 2))
        for index in (self.waveform.start, self.waveform.end):
            x = int(self._x_of(index))
            painter.drawLine(x, rect.top(), x, rect.bottom())


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
        self.overview = ToneOverview(self.samples, self)
        self.overview.bind(self.waveform)
        self.overview.setToolTip(self.tr("Full track overview. Click or drag to move the view."))

        # --- Zoom controls -----------------------------------------------
        self._control_height = max(18, self.fontMetrics().height())
        self._syncing_zoom = False
        self.reset_view_button = self._make_tool_button(
            "reset", self.tr("Reset view"), self.tr("Reset view"))
        self.zoom_out_button = self._make_tool_button(
            "zoom_out", self.tr("Zoom out"), self.tr("Zoom out"))
        self.zoom_in_button = self._make_tool_button(
            "zoom_in", self.tr("Zoom in"), self.tr("Zoom in"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.zoom_slider.setRange(0, 1000)
        self.zoom_slider.setFixedWidth(140)
        self.zoom_slider.setFixedHeight(self._control_height)
        self.zoom_slider.setToolTip(self.tr("Zoom"))
        self.zoom_label = QLabel("100%", self)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.zoom_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.zoom_label.setToolTip(self.tr("Zoom"))

        self.start_box = QDoubleSpinBox(self)
        self.end_box = QDoubleSpinBox(self)
        for box in (self.start_box, self.end_box):
            box.setDecimals(2)
            box.setSingleStep(0.05)
            box.setSuffix(" s")
            box.setMaximum(round(self.samples.size / TONE_SAMPLE_RATE, 2))
            box.setKeyboardTracking(False)   # Apply on focus loss or Enter only
            box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            box.setMinimumWidth(90)
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
        playback.addWidget(self.start_box, 1)
        playback.addWidget(QLabel("→", self))
        playback.addWidget(self.end_box, 1)
        playback.addWidget(self.play_button)
        playback.addWidget(self.duration_label)

        form = QFormLayout()
        form.addRow(self.tr("Start / end"), playback)
        form.addRow(self.tr("Volume"), gain_row)
        form.addRow(self.tr("File Name"), file_row)
        form.addRow(self.tr("Display Name"), self.display_edit)

        hint = QLabel(self.tr("Only the selected range is saved. The 192000-byte limit "
                              "is about 5.7 s at 16755 Hz."), self)
        hint.setWordWrap(True)
        self.gain_hint.setWordWrap(True)
        # Hint labels must keep their natural height; only the waveform absorbs extra window height
        for label in (hint, self.gain_hint):
            label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        zoom_row = QHBoxLayout()
        zoom_row.addStretch(1)
        zoom_row.addWidget(self.reset_view_button)
        zoom_row.addWidget(self.zoom_out_button)
        zoom_row.addWidget(self.zoom_slider)
        zoom_row.addWidget(self.zoom_in_button)
        zoom_row.addWidget(self.zoom_label)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        # Use the application's i18n instead of Qt's qtbase button translations
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("OK"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))

        layout = QVBoxLayout(self)
        layout.addWidget(self.overview)
        layout.addWidget(self.waveform, 1)
        layout.addLayout(zoom_row)
        layout.addLayout(form)
        layout.addWidget(self.gain_hint)
        layout.addWidget(hint)
        layout.addWidget(self.buttons)

        self.waveform.range_changed.connect(self._on_range_changed)
        self.waveform.view_changed.connect(self._on_view_changed)
        self.start_box.editingFinished.connect(self._commit_start_box)
        self.end_box.editingFinished.connect(self._commit_end_box)
        self.play_button.clicked.connect(self._on_play)
        self.gain_slider.value_changed.connect(self._on_slider_moved)
        self.gain_slider.released.connect(self._on_gain_applied)
        self.gain_box.valueChanged.connect(self._on_box_gain_changed)
        self.gain_box.editingFinished.connect(self._on_gain_applied)
        self.auto_gain_check.toggled.connect(self._on_auto_toggled)
        self.reset_view_button.clicked.connect(self.waveform.reset_view)
        self.zoom_out_button.clicked.connect(lambda: self._zoom_step(1.0 / self.waveform.ZOOM_STEP))
        self.zoom_in_button.clicked.connect(lambda: self._zoom_step(self.waveform.ZOOM_STEP))
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.auto_gain_check.setChecked(True)   # Default matches the old behavior: normalize the peak without clipping
        self._on_range_changed(self.waveform.start, self.waveform.end)
        self._on_view_changed(self.waveform.view_start, self.waveform.view_span)

    # --- Sync --------------------------------------------------------
    def _on_range_changed(self, start: int, end: int):
        shown_start = round(start / TONE_SAMPLE_RATE, 2)
        shown_end = round(end / TONE_SAMPLE_RATE, 2)
        for box, value in ((self.start_box, shown_start), (self.end_box, shown_end)):
            box.blockSignals(True)
            box.setValue(value)
            box.blockSignals(False)
        self._box_values = (shown_start, shown_end)
        self.duration_label.setText(f"{(end - start) / TONE_SAMPLE_RATE:.2f} s")
        if self.auto_gain_check.isChecked():
            self._set_gain_controls(self._auto_gain_value(), from_auto=True)
        self._update_gain_hint()

    def _commit_start_box(self):
        """Keep the typed start time and move the end handle only when it cannot follow."""
        if self.start_box.value() == getattr(self, "_box_values", (None, None))[0]:
            return   # Not edited; committing would shift the range by the two-decimal rounding
        start = int(round(self.start_box.value() * TONE_SAMPLE_RATE))
        end = self.waveform.end
        pad = int(round(0.5 * TONE_SAMPLE_RATE))
        if abs(end - start) > TONE_MAX_SAMPLES:
            end = min(self.waveform.total, start + pad)
        elif end < start:
            start, end = end, start
        self.waveform.set_range(max(0, min(start, self.waveform.total)),
                                max(0, min(end, self.waveform.total)))
        self._on_range_changed(self.waveform.start, self.waveform.end)

    def _commit_end_box(self):
        """Keep the typed end time and move the start handle only when it cannot follow."""
        if self.end_box.value() == getattr(self, "_box_values", (None, None))[1]:
            return
        end = int(round(self.end_box.value() * TONE_SAMPLE_RATE))
        start = self.waveform.start
        pad = int(round(0.5 * TONE_SAMPLE_RATE))
        if abs(end - start) > TONE_MAX_SAMPLES:
            start = max(0, end - pad)
        elif start > end:
            start, end = end, start
        self.waveform.set_range(max(0, min(start, self.waveform.total)),
                                max(0, min(end, self.waveform.total)))
        self._on_range_changed(self.waveform.start, self.waveform.end)

    # --- View --------------------------------------------------------
    def _on_view_changed(self, start: int, span: int):
        self.overview.update()
        zoom = self.waveform.zoom
        percent = int(round(zoom * 100))
        if percent >= 10000:
            # Huge magnifications read better as a multiplier than as six-digit percentages
            self.zoom_label.setText(f"{zoom:.2f}x")
        else:
            self.zoom_label.setText(f"{percent}%")
        low, high = 1.0, self.waveform.max_zoom
        self._syncing_zoom = True
        if high > low:
            ratio = max(0.0, min(1.0, math.log(zoom / low) / math.log(high / low)))
            self.zoom_slider.setValue(int(round(ratio * 1000)))
        else:
            self.zoom_slider.setValue(0)
        self._syncing_zoom = False

    def _zoom_step(self, factor: float):
        self.waveform.set_zoom(self.waveform.zoom * factor)

    def _on_zoom_slider(self, value: int):
        if self._syncing_zoom:
            return
        low, high = 1.0, self.waveform.max_zoom
        if high <= low:
            return
        self.waveform.set_zoom(low * (high / low) ** (value / 1000.0))

    def _make_tool_button(self, kind: str, tooltip: str, text: str = "") -> QToolButton:
        """Small borderless icon button sized to the text line; hover/pressed states come from the stylesheet."""
        button = QToolButton(self)
        button.setAutoRaise(True)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setIcon(self._tool_icon(kind))
        button.setIconSize(QSize(14, 14))
        button.setFixedSize(self._control_height + 6, self._control_height)
        button.setToolTip(tooltip)
        button.setAccessibleName(text or tooltip)
        button.setStyleSheet(
            "QToolButton { border: none; background: transparent; padding: 0; border-radius: 3px; }"
            "QToolButton:hover { background: palette(midlight); }"
            "QToolButton:pressed { background: palette(mid); }"
        )
        return button

    def _tool_icon(self, kind: str) -> QIcon:
        """Paint the zoom icons in the text color so they follow the current theme."""
        color = self.palette().color(QPalette.ColorRole.WindowText)
        pixmap = QPixmap(14, 14)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(color, 1.4))
        if kind == "reset":
            # Double-headed arrow: fit the whole track into the view
            painter.drawLine(2, 7, 12, 7)
            painter.drawLine(2, 7, 4, 5)
            painter.drawLine(2, 7, 4, 9)
            painter.drawLine(12, 7, 10, 5)
            painter.drawLine(12, 7, 10, 9)
        else:
            painter.drawEllipse(1, 1, 8, 8)
            painter.drawLine(9, 9, 12, 12)
            painter.drawLine(3, 5, 7, 5)
            if kind == "zoom_in":
                painter.drawLine(5, 3, 5, 7)
        painter.end()
        return QIcon(pixmap)


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
    def accept(self):
        # A time box may still hold uncommitted text when OK is clicked; commit it
        # before the dialog closes so the saved range matches what the user sees.
        self.start_box.interpretText()
        self.end_box.interpretText()
        self._commit_start_box()
        self._commit_end_box()
        super().accept()

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
