"""Self-painted battery curve widget with time-axis zoom and pan."""
from __future__ import annotations

import math
from datetime import datetime, timezone

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QApplication, QSizePolicy, QWidget

from .model import (
    CHANNEL_LABELS,
    CHANNELS,
    DEFAULT_WINDOW_SECONDS,
    Viewport,
    decimate_samples,
)

SERIES_COLORS = {
    "left": QColor("#3b82f6"),
    "right": QColor("#f59e0b"),
    "case": QColor("#10b981"),
}


class BatteryChartWidget(QWidget):
    """Draws up to three battery lines and supports wheel-zoom / drag-pan."""

    MARGIN_LEFT = 52
    MARGIN_RIGHT = 30
    MARGIN_TOP = 36
    MARGIN_BOTTOM = 34

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session = None
        self._visible_channels = set(CHANNELS)
        self._viewport = Viewport(0.0, 10.0, follow=True)
        self._drag_x: float | None = None
        self._drag_y: float | None = None
        self.setMinimumHeight(280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def sizeHint(self) -> QSize:
        return QSize(640, 340)

    def set_session(self, session):
        self._session = session
        self.reset_view()

    def set_visible_channels(self, channels):
        self._visible_channels = {channel for channel in channels if channel in CHANNELS}
        self.update()

    @property
    def viewport(self) -> Viewport:
        return self._viewport

    @property
    def visible_channels(self) -> set[str]:
        return set(self._visible_channels)

    def session_end(self) -> float:
        if self._session is None or not self._session.samples:
            return 10.0
        return max(10.0, self._session.duration_s)

    def reset_view(self):
        if self._session is not None and self._session.samples:
            self._viewport = Viewport(0.0, self.session_end(), follow=True).follow_tail(
                self.session_end(), DEFAULT_WINDOW_SECONDS
            )
        else:
            self._viewport = Viewport(0.0, DEFAULT_WINDOW_SECONDS, follow=True)
        self.update()

    def notify_samples_added(self):
        if self._viewport.follow:
            self._viewport = self._viewport.follow_tail(
                self.session_end(), DEFAULT_WINDOW_SECONDS
            )
        else:
            self._viewport = self._viewport.clamped(self.session_end())
        self.update()

    def fit_view(self):
        self._viewport = self._viewport.fit(self.session_end())
        self.update()

    def follow_latest(self, window: float = DEFAULT_WINDOW_SECONDS):
        span = max(1.0, min(float(window), self.session_end()))
        self._viewport = Viewport(0.0, span, follow=True).follow_tail(
            self.session_end(), span
        )
        self.update()

    def zoom(self, factor: float):
        chart = self.chart_rect()
        anchor = self._viewport.start + self._viewport.span / 2
        self._viewport = self._viewport.zoom_at(anchor, factor, self.session_end())
        self.update()

    def chart_rect(self) -> QRectF:
        return QRectF(
            float(self.MARGIN_LEFT),
            float(self.MARGIN_TOP),
            max(1.0, float(self.width() - self.MARGIN_LEFT - self.MARGIN_RIGHT)),
            max(1.0, float(self.height() - self.MARGIN_TOP - self.MARGIN_BOTTOM)),
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.palette().base())

        chart = self.chart_rect()
        if chart.width() <= 2 or chart.height() <= 2:
            return

        text_color = self.palette().text().color()
        grid_color = QColor(text_color)
        grid_color.setAlpha(45)
        border_color = QColor(text_color)
        border_color.setAlpha(90)

        if self._session is None or not self._session.samples:
            painter.setPen(QPen(text_color))
            painter.drawText(
                chart,
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                QApplication.translate("OfbQtBatteryChart", "No data yet. Start recording to draw a curve."),
            )
            self._draw_border(painter, chart, border_color)
            return

        start = self._viewport.start
        end = self._viewport.end
        if end <= start:
            end = start + 10.0
        span = end - start

        painter.save()
        painter.setClipRect(chart)
        self._draw_disconnected_bands(painter, chart, start, end)
        painter.restore()

        # Grid labels live in the margins, outside chart; draw them after
        # restoring the clip. Series still need the chart clip because decimation
        # can retain one point just outside the viewport.
        self._draw_grid(painter, chart, start, end, text_color, grid_color)
        painter.save()
        painter.setClipRect(chart)
        self._draw_series(painter, chart, start, end)
        painter.restore()

        self._draw_legend(painter, chart, text_color)
        self._draw_border(painter, chart, border_color)

    def _draw_border(self, painter: QPainter, chart: QRectF, color: QColor):
        painter.setPen(QPen(color, 1.0))
        painter.drawRect(chart)

    def _draw_disconnected_bands(self, painter: QPainter, chart: QRectF, start: float, end: float):
        samples = decimate_samples(
            self._session.samples, start, end, max_points=max(100, int(chart.width() * 2))
        )
        band_color = QColor(128, 128, 128, 48)
        for index, sample in enumerate(samples):
            if sample.connected:
                continue
            seg_start = max(start, sample.elapsed_s)
            if seg_start >= end:
                continue
            if index + 1 < len(samples):
                seg_end = min(end, max(sample.elapsed_s, samples[index + 1].elapsed_s))
            else:
                seg_end = end
            if seg_end <= seg_start:
                continue
            x1 = self._map_x(seg_start, chart, start, end)
            x2 = self._map_x(seg_end, chart, start, end)
            painter.fillRect(QRectF(x1, chart.top(), max(1.0, x2 - x1), chart.height()), band_color)

    def _draw_grid(
            self, painter: QPainter, chart: QRectF, start: float, end: float, text_color: QColor, grid_color: QColor
    ):
        font = QFont(self.font())
        font.setPointSizeF(9.0)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        painter.setPen(QPen(grid_color, 1.0))

        for percent in range(0, 101, 10):
            y = self._map_y(percent, chart)
            painter.drawLine(QPointF(chart.left(), y), QPointF(chart.right(), y))
            label = f"{percent}%"
            painter.setPen(QPen(text_color))
            painter.drawText(
                QRectF(0, y - 8, self.MARGIN_LEFT - 7, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label,
            )
            painter.setPen(QPen(grid_color))

        step = _nice_time_step(end - start)
        tick = math.ceil(start / step) * step
        while tick <= end + 1e-9:
            x = self._map_x(tick, chart, start, end)
            painter.drawLine(QPointF(x, chart.top()), QPointF(x, chart.bottom()))
            label = _format_clock(self._session.start_wall, tick, end - start)
            width = max(50, metrics.horizontalAdvance(label) + 8)
            painter.setPen(QPen(text_color))
            painter.drawText(
                QRectF(x - width / 2, chart.bottom() + 6, width, 18),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )
            painter.setPen(QPen(grid_color))
            tick += step

    def _draw_series(self, painter: QPainter, chart: QRectF, start: float, end: float):
        max_points = max(100, int(chart.width() * 2))
        samples = decimate_samples(self._session.samples, start, end, max_points)
        for channel in CHANNELS:
            if channel not in self._visible_channels:
                continue
            path = QPainterPath()
            segment_open = False
            points: list[QPointF] = []
            for sample in samples:
                value = sample.value(channel)
                if value is None:
                    segment_open = False
                    continue
                point = QPointF(
                    self._map_x(sample.elapsed_s, chart, start, end),
                    self._map_y(value, chart),
                )
                points.append(point)
                if not segment_open:
                    path.moveTo(point)
                    segment_open = True
                else:
                    path.lineTo(point)

            pen = QPen(SERIES_COLORS[channel], 1.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)
            if len(points) == 1:
                # A single sample has no line segment; show it as a dot.
                painter.setBrush(SERIES_COLORS[channel])
                painter.drawEllipse(points[0], 2.5, 2.5)
                painter.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_legend(self, painter: QPainter, chart: QRectF, text_color: QColor):
        font = QFont(self.font())
        font.setPointSizeF(9.0)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        entries = [
            (channel, QApplication.translate("OfbQtBatteryChart", CHANNEL_LABELS[channel]))
            for channel in CHANNELS
            if channel in self._visible_channels
        ]
        if not entries:
            return

        line_width = 22
        gap = 8
        item_gap = 18
        widths = [line_width + gap + metrics.horizontalAdvance(label) for _, label in entries]
        total = sum(widths) + item_gap * (len(entries) - 1) + 16
        height = metrics.height() + 10
        # Keep the legend in the top gutter; drawing it inside the plot hides
        # the 90-100% part of the curve when batteries are nearly full.
        box = QRectF(chart.left() + 8, 4, min(total, chart.width() - 16), height)
        background = QColor(self.palette().base())
        background.setAlpha(225)
        painter.fillRect(box, background)
        painter.setPen(QPen(QColor(text_color.red(), text_color.green(), text_color.blue(), 90), 1.0))
        painter.drawRect(box)

        x = box.left() + 8
        y = box.center().y()
        for (channel, label), width in zip(entries, widths):
            painter.setPen(QPen(SERIES_COLORS[channel], 2.2))
            painter.drawLine(QPointF(x, y), QPointF(x + line_width, y))
            painter.setPen(QPen(text_color))
            painter.drawText(
                QRectF(x + line_width + gap, box.top() + 5, width, height - 10),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                label,
            )
            x += width + item_gap

    def _map_x(self, elapsed: float, chart: QRectF, start: float, end: float) -> float:
        return chart.left() + (elapsed - start) / max(1e-9, end - start) * chart.width()

    @staticmethod
    def _map_y(percent: float, chart: QRectF) -> float:
        return chart.top() + (1.0 - max(0.0, min(100.0, percent)) / 100.0) * chart.height()

    def wheelEvent(self, event):
        if self._session is None or not self._session.samples:
            return
        chart = self.chart_rect()
        pos = event.position()
        if not chart.contains(pos):
            return
        delta = event.angleDelta().y()
        if delta == 0:
            return
        anchor = self._viewport.time_at_x(pos.x() - chart.left(), chart.width())
        factor = 0.8 if delta > 0 else 1.25
        self._viewport = self._viewport.zoom_at(anchor, factor, self.session_end())
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        chart = self.chart_rect()
        if event.button() == Qt.MouseButton.LeftButton and chart.contains(event.position()):
            self._drag_x = event.position().x()
            self._drag_y = event.position().y()
            self._viewport.follow = False
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_x is None:
            super().mouseMoveEvent(event)
            return
        chart = self.chart_rect()
        dx = event.position().x() - self._drag_x
        self._drag_x = event.position().x()
        self._drag_y = event.position().y()
        self._viewport = self._viewport.pan_by_pixels(dx, chart.width(), self.session_end())
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_x is not None:
            self._drag_x = None
            self._drag_y = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.chart_rect().contains(event.position()):
            self.fit_view()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._viewport = self._viewport.clamped(self.session_end())
        self.update()


def _nice_time_step(span: float) -> float:
    target = max(1.0, span / 6.0)
    candidates = (
        1, 2, 5, 10, 15, 30, 60, 120, 300, 600,
        900, 1800, 3600, 7200, 21600, 43200, 86400,
    )
    for candidate in candidates:
        if candidate >= target:
            return float(candidate)
    return 86400.0


def _format_clock(start_wall: float, elapsed: float, span: float) -> str:
    timestamp = start_wall + max(0.0, elapsed)
    try:
        moment = datetime.fromtimestamp(timestamp).astimezone()
    except (OSError, OverflowError, ValueError):
        # Windows rejects some pre-1970 timestamps; keep painting instead of
        # letting an exception escape a Qt virtual method.
        moment = datetime.fromtimestamp(timestamp, timezone.utc)
    if span < 60:
        return moment.strftime("%H:%M:%S")
    if span < 6 * 3600:
        return moment.strftime("%H:%M")
    return moment.strftime("%m-%d %H:%M")
