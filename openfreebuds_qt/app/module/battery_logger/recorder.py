"""Async battery sampling and disconnect-state handling."""
from __future__ import annotations

import asyncio
import time
from contextlib import suppress
from typing import Callable

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.utils.logger import create_logger

from .model import (
    CHANNELS,
    DEFAULT_SAMPLE_INTERVAL,
    MAX_SAMPLE_INTERVAL,
    MIN_SAMPLE_INTERVAL,
    BatterySample,
    BatterySession,
    parse_battery,
)

log = create_logger("OfbBatteryLoggerRecorder")


class BatteryRecorderError(RuntimeError):
    pass


class BatteryRecorder:
    """Owns a recording session and its two async loops.

    The recorder subscribes to core events itself instead of relying on the
    settings window's update loop. This is required because the main window
    cancels its event loop when hidden to the tray, while recording should
    continue in the background.
    """

    def __init__(
            self,
            ofb,
            *,
            session: BatterySession | None = None,
            on_update: Callable[[], None] | None = None,
            subscribe_events: bool = True,
            monotonic=time.monotonic,
            wall_clock=time.time,
    ):
        self.ofb = ofb
        self.session = session or BatterySession()
        self.on_update = on_update
        self._subscribe_events = subscribe_events
        self._monotonic = monotonic
        self._wall_clock = wall_clock

        self._running = False
        self._interval_s = float(DEFAULT_SAMPLE_INTERVAL)
        self._tick_task: asyncio.Task | None = None
        self._event_task: asyncio.Task | None = None
        self._member_id: str | None = None
        self._lock = asyncio.Lock()
        self._last_connected: bool | None = None
        self._last_state: int | None = None
        self._stop_reason = ""
        self._last_error = ""
        self._event_error = ""
        self._device_identity = ""
        self._device_name = ""

    @property
    def running(self) -> bool:
        return self._running

    @property
    def interval_s(self) -> float:
        return self._interval_s

    @property
    def stop_reason(self) -> str:
        return self._stop_reason

    @property
    def last_error(self) -> str:
        return self._last_error or self._event_error

    @property
    def device_name(self) -> str:
        return self._device_name

    @property
    def last_connected(self) -> bool | None:
        return self._last_connected

    async def start(self, interval_s: int | float, channels=CHANNELS):
        if self._running:
            raise BatteryRecorderError("Recording is already running")
        interval = int(interval_s)
        if interval < MIN_SAMPLE_INTERVAL or interval > MAX_SAMPLE_INTERVAL:
            raise BatteryRecorderError(
                f"Sampling interval must be {MIN_SAMPLE_INTERVAL}-{MAX_SAMPLE_INTERVAL} seconds"
            )
        selected = frozenset(channel for channel in channels if channel in CHANNELS)
        if not selected:
            raise BatteryRecorderError("Select at least one channel")

        state = await self.ofb.get_state()
        if state != IOpenFreebuds.STATE_CONNECTED:
            raise BatteryRecorderError("Connect the device before starting")

        tags = await self.ofb.get_device_tags()
        device_name, device_address = _normalize_tags(tags)
        self._device_name = device_name
        self._device_identity = device_address or device_name
        self.session.clear()
        self.session.device_name = device_name
        self.session.device_address = device_address
        self.session.enabled_channels = selected
        self.session.reset_clock(start_wall=self._wall_clock(), start_mono=self._monotonic())
        self._interval_s = float(interval)
        self._stop_reason = ""
        self._last_error = ""
        self._event_error = ""
        self._last_connected = None
        self._last_state = state
        self._running = True

        if self._subscribe_events:
            try:
                self._member_id = await self.ofb.subscribe(
                    kind_filters=[OfbEventKind.STATE_CHANGED, OfbEventKind.DEVICE_CHANGED]
                )
                self._event_task = asyncio.create_task(self._event_loop())
            except Exception as exc:
                self._member_id = None
                self._event_task = None
                self._event_error = f"Event subscription unavailable: {exc}"
                log.warning(self._event_error)

        try:
            await self.sample_once(reason="start")
        except Exception:
            await self.stop(reason="start_failed")
            raise

        self._tick_task = asyncio.create_task(self._tick_loop())
        self._notify()
        return True

    async def stop(self, reason: str = "user"):
        if not self._running:
            return
        self._running = False
        self._stop_reason = reason

        current = asyncio.current_task()
        tasks = [task for task in (self._tick_task, self._event_task) if task is not None]
        for task in tasks:
            if task is not current:
                task.cancel()
        for task in tasks:
            if task is current:
                continue
            with suppress(asyncio.CancelledError, Exception):
                await task

        self._tick_task = None
        self._event_task = None
        if self._member_id is not None:
            member_id = self._member_id
            self._member_id = None
            try:
                await self.ofb.unsubscribe(member_id)
            except Exception:
                log.debug("Failed to unsubscribe battery logger", exc_info=True)
        self._notify()

    async def sample_once(self, reason: str = "tick") -> BatterySample | None:
        if not self._running:
            return None
        async with self._lock:
            if not self._running:
                return None
            try:
                state = await self.ofb.get_state()
            except Exception as exc:
                self._last_error = f"Failed to read connection state: {exc}"
                self._last_state = None
                return self._append_zero(reason, error=self._last_error)

            self._last_state = state
            if state == IOpenFreebuds.STATE_PAUSED:
                # Internal operations pause the driver; this is not a disconnect.
                self._last_error = ""
                self._notify()
                return None

            connected = state == IOpenFreebuds.STATE_CONNECTED
            if not connected:
                self._last_error = ""
                return self._append_zero(reason)

            try:
                battery = await self.ofb.get_property("battery")
            except Exception as exc:
                self._last_error = f"Failed to read battery: {exc}"
                values = parse_battery(None, self.session.enabled_channels)
                return self._append_values(values, connected=True, reason=reason, error=self._last_error)

            values = parse_battery(battery, self.session.enabled_channels)
            if not isinstance(battery, dict):
                self._last_error = "Battery data unavailable"
            else:
                self._last_error = ""
            return self._append_values(values, connected=True, reason=reason, error=self._last_error)

    async def _tick_loop(self):
        loop = asyncio.get_running_loop()
        next_at = loop.time() + self._interval_s
        try:
            while self._running:
                delay = next_at - loop.time()
                if delay > 0:
                    await asyncio.sleep(delay)
                if not self._running:
                    break
                await self.sample_once(reason="tick")
                now = loop.time()
                next_at += self._interval_s
                if next_at <= now:
                    # A slow read must not produce a burst of catch-up samples.
                    next_at = now + self._interval_s
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Battery logger tick loop failed")
            self._last_error = "Sampling loop failed"
            asyncio.create_task(self.stop(reason="error"))

    async def _event_loop(self):
        try:
            while self._running and self._member_id is not None:
                kind, *args = await self.ofb.wait_for_event(self._member_id)
                if kind == OfbEventKind.STATE_CHANGED:
                    await self._on_state_event(args)
                elif kind == OfbEventKind.DEVICE_CHANGED:
                    await self._on_device_event()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.debug("Battery logger event loop ended", exc_info=True)
            if self._running:
                self._event_error = "Event subscription ended; interval polling only"
                self._notify()

    async def _on_state_event(self, args):
        if not self._running:
            return
        state = args[0] if args and isinstance(args[0], int) else None
        if state is None:
            try:
                state = await self.ofb.get_state()
            except Exception as exc:
                self._last_error = f"Failed to read connection state: {exc}"
                await self.sample_once(reason="state")
                return
        if state == IOpenFreebuds.STATE_PAUSED:
            self._last_state = state
            self._notify()
            return
        connected = state == IOpenFreebuds.STATE_CONNECTED
        previous = self._last_connected
        if previous is None or connected != previous:
            # sample_once reads the authoritative state and inserts exactly
            # one transition sample (zero on disconnect, real values on resume).
            await self.sample_once(reason="state")

    async def _on_device_event(self):
        if not self._running:
            return
        try:
            tags = await self.ofb.get_device_tags()
        except Exception:
            log.debug("Failed to read device tags", exc_info=True)
            return
        name, address = _normalize_tags(tags)
        identity = address or name
        if self._device_identity and identity and identity != self._device_identity:
            self._last_error = "Device changed; recording stopped"
            asyncio.create_task(self.stop(reason="device_changed"))

    def _append_zero(self, reason: str, error: str = "") -> BatterySample:
        return self._append_values(
            {"left": 0, "right": 0, "case": 0},
            connected=False,
            reason=reason,
            error=error,
        )

    def _append_values(
            self,
            values: dict[str, int | None],
            *,
            connected: bool,
            reason: str,
            error: str = "",
    ) -> BatterySample:
        sample = self.session.add_sample(
            left=values.get("left"),
            right=values.get("right"),
            case=values.get("case"),
            connected=connected,
            elapsed_s=self.session.elapsed(self._monotonic()),
            wall_time=self._wall_clock(),
        )
        self._last_connected = connected
        self._last_error = error
        self._notify(reason)
        return sample

    def _notify(self, *_):
        if self.on_update is None:
            return
        try:
            self.on_update()
        except Exception:
            log.exception("Battery logger update callback failed")


def _normalize_tags(tags) -> tuple[str, str]:
    if not tags:
        return "", ""
    if isinstance(tags, str):
        return tags, ""
    try:
        name, address = tags
        return str(name or ""), str(address or "")
    except (TypeError, ValueError):
        return "", ""
