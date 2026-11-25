"""Tests for the battery logger model, recorder, chart and page."""
import asyncio
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds_qt.app.module.battery_logger.model import (
    CHANNELS,
    CSV_HEADER,
    BatterySample,
    BatterySession,
    Viewport,
    decimate_samples,
    is_tws_battery,
    parse_battery,
    sample_to_csv_row,
    write_csv,
)
from openfreebuds_qt.app.module.battery_logger.recorder import BatteryRecorder, BatteryRecorderError


@pytest.fixture(scope="module")
def qt_app():
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_parse_battery_accepts_driver_strings_and_rejects_invalid():
    assert parse_battery({"left": "87", "right": 86, "case": "73"}) == {
        "left": 87, "right": 86, "case": 73,
    }
    assert parse_battery({"left": "101", "right": -1, "case": "abc"}) == {
        "left": None, "right": None, "case": None,
    }
    assert parse_battery(None) == {"left": None, "right": None, "case": None}
    assert parse_battery({"left": "87", "right": "86", "case": "73"}, {"left"}) == {
        "left": 87, "right": None, "case": None,
    }
    assert not is_tws_battery({"global": "80"})
    assert is_tws_battery({"left": "87", "right": "86", "case": "73"})


def test_session_adds_disconnect_triple_zero_and_keeps_real_zero_distinct():
    session = BatterySession(start_wall=1000.0, start_mono=10.0)
    session.enabled_channels = frozenset({"left"})
    real = session.add_sample(left=0, right=None, case=None, connected=True, elapsed_s=0.0, wall_time=1_700_000_000.0)
    disconnected = session.add_sample(left=0, right=0, case=0, connected=False, elapsed_s=5.0, wall_time=1_700_000_005.0)
    assert real.connected and real.left == 0
    assert not disconnected.connected
    assert disconnected.left == disconnected.right == disconnected.case == 0
    assert session.duration_s == 5.0


def test_csv_has_fixed_columns_bom_and_disconnect_zero_row(tmp_path):
    session = BatterySession(start_wall=1000.0, start_mono=0.0)
    sample = session.add_sample(left=87, right=86, case=73, connected=True, elapsed_s=0.0, wall_time=1_700_000_000.0)
    disconnected = session.add_sample(left=0, right=0, case=0, connected=False, elapsed_s=5.0, wall_time=1_700_000_005.0)
    row = sample_to_csv_row(sample)
    assert row[1:] == ("0.0", "87", "86", "73", "1")
    assert sample_to_csv_row(disconnected)[1:] == ("5.0", "0", "0", "0", "0")

    path = tmp_path / "log.csv"
    count = write_csv(path, session.samples)
    assert count == 2
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    lines = raw.decode("utf-8-sig").splitlines()
    assert lines[0] == ",".join(CSV_HEADER)
    assert lines[1].split(",")[1:] == ["0.0", "87", "86", "73", "1"]
    assert lines[2].split(",")[1:] == ["5.0", "0", "0", "0", "0"]


def test_csv_keeps_unselected_channel_blank():
    sample = BatterySample(elapsed_s=1.0, wall_time=1_700_000_000.0, left=80, right=None, case=None, connected=True)
    row = sample_to_csv_row(sample)
    assert row[1:] == ("1.0", "80", "", "", "1")


def test_viewport_zoom_anchor_pan_fit_and_follow():
    viewport = Viewport(0.0, 100.0, follow=True)
    zoomed = viewport.zoom_at(50.0, 0.5, 100.0)
    assert zoomed.start == pytest.approx(25.0)
    assert zoomed.end == pytest.approx(75.0)
    assert not zoomed.follow
    assert 50.0 == pytest.approx(zoomed.time_at_x(50.0 / 100.0 * 100.0, 100.0))

    panned = zoomed.pan_by_pixels(10.0, 100.0, 100.0)
    assert panned.start < zoomed.start
    assert panned.end < zoomed.end

    fitted = viewport.fit(100.0)
    assert fitted.start == 0.0
    assert fitted.end == 100.0
    assert not fitted.follow

    followed = viewport.follow_tail(1000.0, 600.0)
    assert followed.start == 400.0
    assert followed.end == 1000.0
    assert followed.follow

    capped = Viewport(0.0, 600.0, follow=False).zoom_at(300.0, 1.25, 100.0)
    assert capped.span == pytest.approx(120.0)
    assert capped.end == pytest.approx(120.0)


def test_decimate_preserves_endpoints_and_transitions():
    samples = [
        BatterySample(
            elapsed_s=float(index),
            wall_time=1_700_000_000.0 + index,
            left=None if 20 <= index < 30 else 80,
            right=70,
            case=60,
            connected=index < 50,
        )
        for index in range(100)
    ]
    out = decimate_samples(samples, 0.0, 99.0, max_points=10)
    assert out[0].elapsed_s == 0.0
    assert out[-1].elapsed_s == 99.0
    assert any(sample.connected for sample in out)
    assert any(not sample.connected for sample in out)
    assert any(sample.left is None for sample in out)
    assert len(out) <= 20


class FakeOfb:
    def __init__(self):
        self.state = IOpenFreebuds.STATE_CONNECTED
        self.battery = {"left": "87", "right": 86, "case": "73"}
        self.tags = ("FreeClip 2", "02:00:00:00:00:01")
        self.state_error = False
        self.battery_error = False
        self.member_id = "battery-logger-test"
        self.events = asyncio.Queue()
        self.unsubscribed = []

    async def get_state(self):
        if self.state_error:
            raise RuntimeError("state failed")
        return self.state

    async def get_property(self, group, prop=None, fallback=None):
        if group == "battery":
            if self.battery_error:
                raise RuntimeError("battery failed")
            return self.battery
        return fallback

    async def get_device_tags(self):
        return self.tags

    async def subscribe(self, kind_filters=None):
        self.events = asyncio.Queue()
        return self.member_id

    async def wait_for_event(self, member_id):
        return await self.events.get()

    async def unsubscribe(self, member_id):
        self.unsubscribed.append(member_id)


async def _start_recorder(fake, channels=CHANNELS, **kwargs):
    recorder = BatteryRecorder(
        fake,
        subscribe_events=False,
        monotonic=lambda: 10.0,
        wall_clock=lambda: 1000.0,
        **kwargs,
    )
    await recorder.start(1, channels)
    return recorder


@pytest.mark.asyncio
async def test_recorder_samples_connected_values_and_selected_channels():
    fake = FakeOfb()
    recorder = await _start_recorder(fake, {"left"})
    try:
        sample = recorder.session.samples[0]
        assert sample.left == 87
        assert sample.right is None
        assert sample.case is None
        assert sample.connected
    finally:
        await recorder.stop()


@pytest.mark.asyncio
async def test_recorder_disconnect_writes_three_zeros_and_reconnect_restores_values():
    fake = FakeOfb()
    recorder = await _start_recorder(fake)
    try:
        fake.state = IOpenFreebuds.STATE_DISCONNECTED
        await recorder._on_state_event([IOpenFreebuds.STATE_DISCONNECTED])
        zero = recorder.session.samples[-1]
        assert (zero.left, zero.right, zero.case) == (0, 0, 0)
        assert not zero.connected

        fake.state = IOpenFreebuds.STATE_CONNECTED
        await recorder._on_state_event([IOpenFreebuds.STATE_CONNECTED])
        resumed = recorder.session.samples[-1]
        assert (resumed.left, resumed.right, resumed.case) == (87, 86, 73)
        assert resumed.connected
    finally:
        await recorder.stop()


@pytest.mark.asyncio
async def test_recorder_paused_state_does_not_write_zero():
    fake = FakeOfb()
    recorder = await _start_recorder(fake)
    try:
        count = len(recorder.session.samples)
        fake.state = IOpenFreebuds.STATE_PAUSED
        await recorder.sample_once()
        assert len(recorder.session.samples) == count
    finally:
        await recorder.stop()


@pytest.mark.asyncio
async def test_recorder_handles_state_and_battery_errors():
    fake = FakeOfb()
    recorder = await _start_recorder(fake)
    try:
        fake.state_error = True
        await recorder.sample_once()
        zero = recorder.session.samples[-1]
        assert (zero.left, zero.right, zero.case) == (0, 0, 0)
        assert not zero.connected

        fake.state_error = False
        fake.battery_error = True
        await recorder.sample_once()
        missing = recorder.session.samples[-1]
        assert missing.connected
        assert missing.left is None and missing.right is None and missing.case is None
    finally:
        await recorder.stop()


@pytest.mark.asyncio
async def test_recorder_stops_on_device_change():
    fake = FakeOfb()
    recorder = await _start_recorder(fake)
    fake.tags = ("Other device", "02:00:00:00:00:02")
    await recorder._on_device_event()
    await asyncio.sleep(0.02)
    assert not recorder.running
    assert recorder.stop_reason == "device_changed"


@pytest.mark.asyncio
async def test_recorder_rejects_disconnected_start():
    fake = FakeOfb()
    fake.state = IOpenFreebuds.STATE_DISCONNECTED
    recorder = BatteryRecorder(fake, subscribe_events=False)
    with pytest.raises(BatteryRecorderError):
        await recorder.start(1, {"left"})


@pytest.mark.asyncio
async def test_recorder_rejects_bad_interval_and_empty_channels():
    fake = FakeOfb()
    recorder = BatteryRecorder(fake, subscribe_events=False)
    with pytest.raises(BatteryRecorderError):
        await recorder.start(0, {"left"})
    with pytest.raises(BatteryRecorderError):
        await recorder.start(5, set())


@pytest.mark.asyncio
async def test_recorder_subscribes_and_unsubscribes_events():
    fake = FakeOfb()
    recorder = BatteryRecorder(
        fake,
        subscribe_events=True,
        monotonic=lambda: 10.0,
        wall_clock=lambda: 1000.0,
    )
    await recorder.start(1, CHANNELS)
    try:
        assert recorder._member_id == fake.member_id
        assert recorder._event_task is not None
    finally:
        await recorder.stop()
    assert fake.unsubscribed == [fake.member_id]


@pytest.mark.asyncio
async def test_recorder_clears_transient_read_error_after_success():
    fake = FakeOfb()
    recorder = await _start_recorder(fake)
    try:
        fake.battery_error = True
        await recorder.sample_once()
        assert recorder.last_error
        fake.battery_error = False
        await recorder.sample_once()
        assert recorder.last_error == ""
    finally:
        await recorder.stop()


def test_chart_grab_and_viewport_controls(qt_app):
    print("chart test start", flush=True)
    from openfreebuds_qt.app.module.battery_logger.chart import BatteryChartWidget
    print("chart imported", flush=True)

    session = BatterySession(start_wall=1_700_000_000.0, start_mono=0.0)
    for index in range(10):
        session.add_sample(
            left=90 - index,
            right=89 - index,
            case=80,
            connected=index < 7,
            elapsed_s=float(index * 5),
            wall_time=1_700_000_000.0 + index * 5,
        )
    print("samples built", flush=True)

    chart = BatteryChartWidget()
    print("chart built", flush=True)
    chart.resize(800, 400)
    chart.set_session(session)
    chart.set_visible_channels({"left", "right"})
    print("before grab", flush=True)
    assert not chart.grab().isNull()
    print("after grab", flush=True)

    old_span = chart.viewport.span
    chart.zoom(0.8)
    assert chart.viewport.span < old_span
    chart.fit_view()
    assert chart.viewport.start == 0.0
    chart.follow_latest()
    assert chart.viewport.follow
    chart.deleteLater()
    print("chart test end", flush=True)


def test_chart_grab_single_sample_and_disconnect(qt_app):
    from openfreebuds_qt.app.module.battery_logger.chart import BatteryChartWidget

    session = BatterySession(start_wall=1_700_000_000.0, start_mono=0.0)
    session.add_sample(left=80, right=79, case=70, connected=True, elapsed_s=0.0, wall_time=1_700_000_000.0)
    chart = BatteryChartWidget()
    chart.resize(480, 300)
    chart.set_session(session)
    assert not chart.grab().isNull()

    session.add_sample(left=0, right=0, case=0, connected=False, elapsed_s=5.0, wall_time=1_700_000_005.0)
    chart.notify_samples_added()
    assert not chart.grab().isNull()
    chart.deleteLater()


@pytest.mark.asyncio
async def test_module_allows_start_before_battery_data(qt_app):
    from openfreebuds_qt.app.module.battery_logger.module import OfbQtBatteryLoggerModule

    fake = FakeOfb()
    fake.battery = None
    module = OfbQtBatteryLoggerModule(None, SimpleNamespace(ofb=fake))
    await module._refresh_availability()
    module._refresh_ui()
    assert module.start_button.isEnabled()
    assert not module._battery_data_known
    assert "Waiting for battery data" in module.status_label.text()
    module.deleteLater()


@pytest.mark.asyncio
async def test_module_disables_start_for_non_tws_battery(qt_app):
    from openfreebuds_qt.app.module.battery_logger.module import OfbQtBatteryLoggerModule

    fake = FakeOfb()
    fake.battery = {"global": "80"}
    module = OfbQtBatteryLoggerModule(None, SimpleNamespace(ofb=fake))
    await module._refresh_availability()
    module._refresh_ui()
    assert module._battery_non_tws
    assert not module.start_button.isEnabled()
    assert "does not report separate" in module.detail_label.text()
    module.deleteLater()


def test_module_constructs_with_fake_context(qt_app):
    from openfreebuds_qt.app.module.battery_logger.module import OfbQtBatteryLoggerModule

    fake = FakeOfb()
    module = OfbQtBatteryLoggerModule(None, SimpleNamespace(ofb=fake))
    assert module._interval() == 5
    assert module._selected_channels() == set(CHANNELS)
    assert not module.start_button.isEnabled()  # no asynchronous availability refresh yet
    module.deleteLater()
