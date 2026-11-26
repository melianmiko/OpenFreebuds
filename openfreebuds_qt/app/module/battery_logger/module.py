"""Settings page for recording and exporting OpenFreebuds battery curves."""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QStandardPaths, Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget,
)
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.utils.qt_utils import exec_msg_box_async

from .chart import BatteryChartWidget
from .model import (
    DEFAULT_SAMPLE_INTERVAL,
    MAX_SAMPLE_INTERVAL,
    MIN_SAMPLE_INTERVAL,
    SOFT_SAMPLE_LIMIT,
    format_duration,
    is_tws_battery,
    write_csv,
)
from .recorder import BatteryRecorder, BatteryRecorderError


class OfbQtBatteryLoggerModule(OfbQtCommonModule):
    """UI wrapper around BatteryRecorder; the recorder keeps running when hidden."""

    def __init__(self, parent: QWidget, context):
        super().__init__(parent, context)
        self._available_state: int | None = None
        self._battery_available = False
        self._battery_data_known = False
        self._battery_non_tws = False
        self._device_tags = ("", "")
        self.recorder = BatteryRecorder(self.ofb, on_update=self._on_recorder_update)
        self._build_ui()
        self._refresh_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        controls = QGroupBox(self.tr("Recording controls"))
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_layout.setSpacing(8)

        first_row = QHBoxLayout()
        self.start_button = QPushButton(self.tr("Start recording"))
        self.start_button.setDefault(True)
        self.start_button.clicked.connect(self.on_toggle_recording)
        first_row.addWidget(self.start_button)

        first_row.addSpacing(10)
        first_row.addWidget(QLabel(self.tr("Sampling interval")))
        self.interval_combo = QComboBox()
        for label, seconds in (
                ("1 s", 1),
                ("2 s", 2),
                ("5 s", 5),
                ("10 s", 10),
                ("30 s", 30),
                ("60 s", 60),
                (self.tr("Custom…"), None),
        ):
            self.interval_combo.addItem(label, seconds)
        self.interval_combo.setCurrentIndex(2)
        self.interval_combo.currentIndexChanged.connect(self.on_interval_changed)
        first_row.addWidget(self.interval_combo)

        self.custom_interval = QSpinBox()
        self.custom_interval.setRange(MIN_SAMPLE_INTERVAL, MAX_SAMPLE_INTERVAL)
        self.custom_interval.setValue(DEFAULT_SAMPLE_INTERVAL)
        self.custom_interval.setSuffix(" s")
        self.custom_interval.setVisible(False)
        first_row.addWidget(self.custom_interval)

        first_row.addStretch(1)
        self.export_button = QPushButton(self.tr("Export CSV"))
        self.export_button.clicked.connect(self.on_export)
        first_row.addWidget(self.export_button)
        self.clear_button = QPushButton(self.tr("Clear"))
        self.clear_button.clicked.connect(self.on_clear)
        first_row.addWidget(self.clear_button)
        controls_layout.addLayout(first_row)

        channels_row = QHBoxLayout()
        channels_row.addWidget(QLabel(self.tr("Channels")))
        self.left_check = QCheckBox(self.tr("Left earbud"))
        self.right_check = QCheckBox(self.tr("Right earbud"))
        self.case_check = QCheckBox(self.tr("Charging case"))
        for check in (self.left_check, self.right_check, self.case_check):
            check.setChecked(True)
            check.toggled.connect(self.on_channels_changed)
            channels_row.addWidget(check)
        channels_row.addStretch(1)
        controls_layout.addLayout(channels_row)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        controls_layout.addWidget(self.status_label)
        self.detail_label = QLabel()
        self.detail_label.setWordWrap(True)
        self.detail_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        controls_layout.addWidget(self.detail_label)
        root.addWidget(controls)

        chart_group = QGroupBox(self.tr("Battery curve"))
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        chart_layout.setSpacing(6)

        toolbar = QHBoxLayout()
        self.fit_button = QPushButton(self.tr("Fit"))
        self.fit_button.clicked.connect(self.on_fit)
        toolbar.addWidget(self.fit_button)
        self.follow_button = QPushButton(self.tr("Follow"))
        self.follow_button.clicked.connect(self.on_follow)
        toolbar.addWidget(self.follow_button)
        self.zoom_in_button = QPushButton(self.tr("Zoom +"))
        self.zoom_in_button.clicked.connect(self.on_zoom_in)
        toolbar.addWidget(self.zoom_in_button)
        self.zoom_out_button = QPushButton(self.tr("Zoom -"))
        self.zoom_out_button.clicked.connect(self.on_zoom_out)
        toolbar.addWidget(self.zoom_out_button)
        toolbar.addStretch(1)
        chart_layout.addLayout(toolbar)

        self.chart = BatteryChartWidget()
        self.chart.set_session(self.recorder.session)
        self.chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chart_layout.addWidget(self.chart, 1)
        root.addWidget(chart_group, 1)

    async def update_ui(self, event: OfbCoreEvent):
        if (event.kind_match(None)
                or event.kind_match(OfbEventKind.STATE_CHANGED)
                or event.is_changed("battery", "")):
            await self._refresh_availability()
        self._refresh_ui()

    def showEvent(self, event):
        super().showEvent(event)
        # The main window update loop may still be busy with other pages.
        # Refresh this page's own readiness so Start is not left disabled.
        try:
            asyncio.create_task(self._refresh_from_page())
        except RuntimeError:
            pass

    async def _refresh_from_page(self):
        await self._refresh_availability()
        self._refresh_ui()

    async def _refresh_availability(self):
        try:
            self._available_state = await self.ofb.get_state()
            self._device_tags = await self.ofb.get_device_tags() or ("", "")
            battery = None
            if self._available_state == IOpenFreebuds.STATE_CONNECTED:
                battery = await self.ofb.get_property("battery")
            self._battery_data_known = isinstance(battery, dict)
            self._battery_available = is_tws_battery(battery)
            self._battery_non_tws = self._battery_data_known and not self._battery_available
        except Exception:
            self._available_state = None
            self._battery_available = False
            self._battery_data_known = False
            self._battery_non_tws = False
            self._device_tags = ("", "")

    def _refresh_ui(self):
        if not hasattr(self, "status_label"):
            return
        running = self.recorder.running
        samples = self.recorder.session.samples
        self.start_button.setText(self.tr("Stop recording") if running else self.tr("Start recording"))
        self.start_button.setEnabled(running or self._can_start())
        self.interval_combo.setEnabled(not running)
        self.custom_interval.setEnabled(not running)
        for check in (self.left_check, self.right_check, self.case_check):
            check.setEnabled(not running)
        self.export_button.setEnabled(bool(samples))
        self.clear_button.setEnabled(bool(samples) and not running)
        self.chart.set_visible_channels(self._selected_channels())

        if running:
            if self.recorder.last_connected:
                text = self.tr("Recording | {interval} s | {count} samples | {duration}").format(
                    interval=int(self.recorder.interval_s),
                    count=len(samples),
                    duration=format_duration(self.recorder.session.duration_s),
                )
            else:
                text = self.tr("Recording | device disconnected - logging 0%")
            self.status_label.setText(text)
        elif self.recorder.stop_reason == "device_changed":
            self.status_label.setText(self.tr("Recording stopped: device changed."))
        elif samples:
            self.status_label.setText(self.tr("Stopped | {count} samples | {duration}").format(
                count=len(samples),
                duration=format_duration(self.recorder.session.duration_s),
            ))
        elif self._available_state == IOpenFreebuds.STATE_CONNECTED and self._battery_available:
            self.status_label.setText(self.tr("Ready to record."))
        elif self._available_state == IOpenFreebuds.STATE_CONNECTED and self._battery_non_tws:
            self.status_label.setText(self.tr("This device does not report separate left/right/case levels."))
        elif self._available_state == IOpenFreebuds.STATE_CONNECTED:
            self.status_label.setText(self.tr("Waiting for battery data…"))
        else:
            self.status_label.setText(self.tr("Waiting for device…"))

        if self._available_state == IOpenFreebuds.STATE_CONNECTED and self._battery_non_tws:
            detail = self.tr("This device does not report separate left/right/case levels.")
        else:
            detail = self._detail_text()
        if self.recorder.last_error:
            detail = f"{detail} | {self.recorder.last_error}"
        self.detail_label.setText(detail)

        if len(samples) >= SOFT_SAMPLE_LIMIT:
            self.status_label.setText(
                f"{self.status_label.text()}  {self.tr('Recording is large; consider exporting and clearing.')}"
            )

    def _detail_text(self) -> str:
        name = self.recorder.device_name
        if not name:
            tags = self._device_tags
            name = tags[0] if isinstance(tags, (tuple, list)) and tags else ""
        name = name or self.tr("No device")
        last = self.recorder.session.last_sample
        if last is None:
            return self.tr("Device: {name}").format(name=name)
        if not last.connected:
            values = self.tr("Last: 0% / 0% / 0% (disconnected)")
        else:
            values = self.tr("Last: L {left} | R {right} | C {case}").format(
                left=_fmt_level(last.left),
                right=_fmt_level(last.right),
                case=_fmt_level(last.case),
            )
        return f"{self.tr('Device: {name}').format(name=name)}  |  {values}"

    def _can_start(self) -> bool:
        # Connected devices may not have published battery data yet; allow
        # recording with blank values until it arrives. A device that has
        # published a non-TWS battery map (no "case") stays disabled.
        data_ready_or_waiting = self._battery_available or not self._battery_data_known
        return (
            not self.recorder.running
            and self._available_state == IOpenFreebuds.STATE_CONNECTED
            and data_ready_or_waiting
            and not self._battery_non_tws
            and bool(self._selected_channels())
        )

    def _selected_channels(self) -> set[str]:
        selected = set()
        if self.left_check.isChecked():
            selected.add("left")
        if self.right_check.isChecked():
            selected.add("right")
        if self.case_check.isChecked():
            selected.add("case")
        return selected

    def _interval(self) -> int:
        value = self.interval_combo.currentData()
        if value is None:
            return int(self.custom_interval.value())
        return int(value)

    def _on_recorder_update(self):
        if hasattr(self, "chart"):
            self.chart.notify_samples_added()
        self._refresh_ui()

    @asyncSlot()
    async def on_toggle_recording(self):
        if self.recorder.running:
            await self.recorder.stop("user")
            self._refresh_ui()
            return

        try:
            state = await self.ofb.get_state()
            battery = await self.ofb.get_property("battery") if state == IOpenFreebuds.STATE_CONNECTED else None
        except Exception as exc:
            await self._show_warning(self.tr("Could not start recording: {error}").format(error=exc))
            return
        if state != IOpenFreebuds.STATE_CONNECTED:
            await self._show_warning(self.tr("Connect a device before recording."))
            return
        if isinstance(battery, dict) and not is_tws_battery(battery):
            await self._show_warning(self.tr("This device does not report separate left/right/case levels."))
            return
        channels = self._selected_channels()
        if not channels:
            await self._show_warning(self.tr("Select at least one channel."))
            return

        if self.recorder.session.samples:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Icon.Question)
            dialog.setWindowTitle("OpenFreebuds")
            dialog.setText(self.tr("A recording already exists. Clear it and start a new one?"))
            dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            dialog.setDefaultButton(QMessageBox.StandardButton.No)
            if int(await exec_msg_box_async(dialog)) != int(QMessageBox.StandardButton.Yes):
                return

        try:
            await self.recorder.start(self._interval(), channels)
            self.chart.reset_view()
            self._refresh_ui()
        except BatteryRecorderError as exc:
            await self._show_warning(str(exc))
        except Exception as exc:
            await self._show_warning(self.tr("Could not start recording: {error}").format(error=exc))

    @asyncSlot()
    async def on_export(self):
        samples = self.recorder.session.snapshot().samples
        if not samples:
            return
        documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        directory = documents or str(Path.home())
        default_name = f"openfreebuds-battery-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export battery log"),
            str(Path(directory) / default_name),
            self.tr("CSV files (*.csv)"),
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() != ".csv":
            target = target.with_suffix(".csv")
        try:
            count = await asyncio.to_thread(write_csv, target, samples)
            self.status_label.setText(self.tr("Exported {count} samples to {path}").format(
                count=count,
                path=str(target),
            ))
        except Exception as exc:
            await self._show_warning(self.tr("Failed to export: {error}").format(error=exc))

    @asyncSlot()
    async def on_clear(self):
        if self.recorder.running or not self.recorder.session.samples:
            return
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setWindowTitle("OpenFreebuds")
        dialog.setText(self.tr("Clear the current recording?"))
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        if int(await exec_msg_box_async(dialog)) != int(QMessageBox.StandardButton.Yes):
            return
        self.recorder.session.clear()
        self.chart.reset_view()
        self._refresh_ui()

    def on_interval_changed(self, *_):
        self.custom_interval.setVisible(self.interval_combo.currentData() is None)
        self._refresh_ui()

    def on_channels_changed(self, *_):
        self.chart.set_visible_channels(self._selected_channels())
        self._refresh_ui()

    def on_fit(self):
        self.chart.fit_view()

    def on_follow(self):
        self.chart.follow_latest()

    def on_zoom_in(self):
        self.chart.zoom(0.8)

    def on_zoom_out(self):
        self.chart.zoom(1.25)

    async def _show_warning(self, text: str):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("OpenFreebuds")
        dialog.setText(text)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        await exec_msg_box_async(dialog)

    def shutdown(self):
        if self.recorder.running:
            asyncio.create_task(self.recorder.stop("shutdown"))


def _fmt_level(value: int | None) -> str:
    return "--" if value is None else f"{value}%"
