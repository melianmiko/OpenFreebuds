"""Data model, CSV export and viewport math for the battery logger.

The module is deliberately UI-free so the sampling semantics can be tested
without a running Qt application.
"""
from __future__ import annotations

import csv
import math
import time
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence

CHANNELS = ("left", "right", "case")
CHANNEL_LABELS = {
    "left": "Left earbud",
    "right": "Right earbud",
    "case": "Charging case",
}
CSV_HEADER = ("timestamp_iso", "elapsed_s", "left", "right", "case", "connected")
MIN_SAMPLE_INTERVAL = 1
MAX_SAMPLE_INTERVAL = 3600
DEFAULT_SAMPLE_INTERVAL = 5
DEFAULT_WINDOW_SECONDS = 600.0
SOFT_SAMPLE_LIMIT = 500_000


@dataclass(slots=True)
class BatterySample:
    """One sampled battery reading.

    ``None`` means "not selected or not reported". A disconnected sample is
    always represented as three real zeros plus ``connected=False``, so a
    disconnect can never be confused with a true 0% reading.
    """

    elapsed_s: float
    wall_time: float
    left: int | None = None
    right: int | None = None
    case: int | None = None
    connected: bool = True

    def value(self, channel: str) -> int | None:
        if channel == "left":
            return self.left
        if channel == "right":
            return self.right
        if channel == "case":
            return self.case
        raise KeyError(channel)


@dataclass(slots=True)
class SessionSnapshot:
    samples: tuple[BatterySample, ...]
    start_wall: float
    start_mono: float
    device_name: str
    device_address: str
    enabled_channels: frozenset[str]


class BatterySession:
    """Mutable in-memory recording session owned by BatteryRecorder."""

    def __init__(
            self,
            *,
            start_wall: float | None = None,
            start_mono: float | None = None,
            enabled_channels: Iterable[str] = CHANNELS,
    ):
        self.samples: list[BatterySample] = []
        self.start_wall = time.time() if start_wall is None else start_wall
        self.start_mono = time.monotonic() if start_mono is None else start_mono
        self.device_name = ""
        self.device_address = ""
        self.enabled_channels = _normalize_channels(enabled_channels)

    def reset_clock(self, *, start_wall: float | None = None, start_mono: float | None = None):
        self.start_wall = time.time() if start_wall is None else start_wall
        self.start_mono = time.monotonic() if start_mono is None else start_mono

    def elapsed(self, monotonic_now: float | None = None) -> float:
        now = time.monotonic() if monotonic_now is None else monotonic_now
        return max(0.0, now - self.start_mono)

    def add_sample(
            self,
            *,
            left: int | None,
            right: int | None,
            case: int | None,
            connected: bool,
            elapsed_s: float | None = None,
            wall_time: float | None = None,
    ) -> BatterySample:
        if elapsed_s is None:
            elapsed_s = self.elapsed()
        if wall_time is None:
            wall_time = time.time()
        sample = BatterySample(
            elapsed_s=max(0.0, float(elapsed_s)),
            wall_time=float(wall_time),
            left=left,
            right=right,
            case=case,
            connected=bool(connected),
        )
        self.samples.append(sample)
        return sample

    def clear(self):
        self.samples.clear()
        self.reset_clock()

    def snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
            samples=tuple(self.samples),
            start_wall=self.start_wall,
            start_mono=self.start_mono,
            device_name=self.device_name,
            device_address=self.device_address,
            enabled_channels=self.enabled_channels,
        )

    @property
    def last_sample(self) -> BatterySample | None:
        return self.samples[-1] if self.samples else None

    @property
    def duration_s(self) -> float:
        if not self.samples:
            return 0.0
        return self.samples[-1].elapsed_s


def _normalize_channels(channels: Iterable[str]) -> frozenset[str]:
    selected = frozenset(channel for channel in channels if channel in CHANNELS)
    return selected or frozenset(CHANNELS)


def _parse_percent(value) -> int | None:
    """Accept the string/int forms used by the Huawei driver, reject invalid data."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        number = value
    elif isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            return None
        number = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = int(text)
        except ValueError:
            try:
                parsed = float(text)
            except ValueError:
                return None
            if not math.isfinite(parsed) or not parsed.is_integer():
                return None
            number = int(parsed)
    else:
        return None
    if 0 <= number <= 100:
        return number
    return None


def parse_battery(battery: dict | None, channels: Iterable[str] = CHANNELS) -> dict[str, int | None]:
    """Return the three normalized levels, with ``None`` for missing/disabled channels."""
    selected = _normalize_channels(channels)
    out: dict[str, int | None] = {channel: None for channel in CHANNELS}
    if not isinstance(battery, dict):
        return out
    for channel in CHANNELS:
        if channel in selected:
            out[channel] = _parse_percent(battery.get(channel))
    return out


def is_tws_battery(battery: dict | None) -> bool:
    return isinstance(battery, dict) and "case" in battery


def format_timestamp(wall_time: float) -> str:
    try:
        moment = datetime.fromtimestamp(wall_time).astimezone()
    except (OSError, OverflowError, ValueError):
        # Windows can reject old timestamps; keep CSV export working.
        moment = datetime.fromtimestamp(wall_time, timezone.utc)
    return moment.isoformat(timespec="seconds")


def sample_to_csv_row(sample: BatterySample) -> tuple[str, ...]:
    def cell(value: int | None) -> str:
        return "" if value is None else str(value)

    return (
        format_timestamp(sample.wall_time),
        f"{sample.elapsed_s:.1f}",
        cell(sample.left),
        cell(sample.right),
        cell(sample.case),
        "1" if sample.connected else "0",
    )


def write_csv(path: str | Path, samples: Iterable[BatterySample]) -> int:
    """Write a UTF-8-BOM CSV and return the number of data rows."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for sample in samples:
            writer.writerow(sample_to_csv_row(sample))
            count += 1
    return count


@dataclass(slots=True)
class Viewport:
    """Time window for the chart; values are elapsed seconds from session start."""

    start: float = 0.0
    end: float = 10.0
    follow: bool = True

    @property
    def span(self) -> float:
        return max(1e-9, self.end - self.start)

    def _limit(self, session_end: float, min_span: float) -> float:
        # Do not let repeated zoom-out requests grow the window without bound.
        return max(min_span, float(session_end)) * 1.2

    def fit(self, session_end: float, min_span: float = 1.0) -> "Viewport":
        end = max(min_span, float(session_end))
        return Viewport(0.0, end, follow=False)

    def follow_tail(
            self, session_end: float, window: float = DEFAULT_WINDOW_SECONDS, min_span: float = 1.0
    ) -> "Viewport":
        end = max(min_span, float(session_end))
        span = min(max(min_span, float(window)), end)
        return Viewport(max(0.0, end - span), end, follow=True)

    def clamped(self, session_end: float, min_span: float = 1.0) -> "Viewport":
        limit = self._limit(session_end, min_span)
        span = min(max(self.span, min_span), limit)
        start = min(max(0.0, self.start), max(0.0, limit - span))
        return Viewport(start, start + span, follow=self.follow)

    def zoom_at(
            self, anchor: float, factor: float, session_end: float, min_span: float = 1.0
    ) -> "Viewport":
        limit = self._limit(session_end, min_span)
        new_span = min(max(self.span * max(0.01, factor), min_span), limit)
        ratio = max(0.0, min(1.0, (anchor - self.start) / self.span))
        new_start = anchor - ratio * new_span
        if new_start < 0:
            new_start = 0.0
        if new_start + new_span > limit:
            new_start = max(0.0, limit - new_span)
        return Viewport(new_start, new_start + new_span, follow=False)

    def pan_by_pixels(self, dx: float, width: float, session_end: float, min_span: float = 1.0) -> "Viewport":
        if width <= 0:
            return self
        delta = -float(dx) * self.span / float(width)
        limit = self._limit(session_end, min_span)
        span = min(max(self.span, min_span), limit)
        start = min(max(0.0, self.start + delta), max(0.0, limit - span))
        return Viewport(start, start + span, follow=False)

    def time_at_x(self, x: float, width: float) -> float:
        if width <= 0:
            return self.start
        ratio = max(0.0, min(1.0, float(x) / float(width)))
        return self.start + ratio * self.span


def _pending_sample_indices(samples: Sequence[BatterySample]) -> set[int]:
    """Keep transitions that must survive downsampling."""
    mandatory = {0, len(samples) - 1}
    for index in range(1, len(samples)):
        previous = samples[index - 1]
        current = samples[index]
        if previous.connected != current.connected:
            mandatory.add(index)
            continue
        for channel in CHANNELS:
            if (previous.value(channel) is None) != (current.value(channel) is None):
                mandatory.add(index)
                break
    return mandatory


def decimate_samples(
        samples: Sequence[BatterySample],
        start: float,
        end: float,
        max_points: int,
) -> list[BatterySample]:
    """Return a viewport slice, downsampled while preserving transitions."""
    if not samples:
        return []
    max_points = max(2, int(max_points))
    left = max(0, bisect_left(samples, start, key=lambda sample: sample.elapsed_s) - 1)
    right = min(len(samples), bisect_right(samples, end, key=lambda sample: sample.elapsed_s) + 1)
    visible = list(samples[left:right])
    if len(visible) <= max_points:
        return visible

    mandatory = _pending_sample_indices(visible)
    step = max(1, math.ceil((len(visible) - 1) / max(1, max_points - 1)))
    indices = set(range(0, len(visible), step))
    indices.add(len(visible) - 1)
    indices.update(mandatory)
    return [visible[index] for index in sorted(indices)]


def iter_samples_in_range(
        samples: Sequence[BatterySample], start: float, end: float
) -> Iterator[BatterySample]:
    for sample in decimate_samples(samples, start, end, max_points=len(samples) or 2):
        if sample.elapsed_s < start or sample.elapsed_s > end:
            continue
        yield sample


def format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
