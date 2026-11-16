import json
import os
import tempfile
import wave
from html import escape as html_escape
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QSizePolicy
from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds.driver.huawei.prompt_tone import convert_to_tone_pcm
from openfreebuds.driver.huawei.tone_library import ToneLibrary, ToneLibraryError
from openfreebuds_qt.app.dialog.tone_editor import OfbQtToneEditorDialog
from openfreebuds_qt.qt_i18n import get_prompt_tone_name
from openfreebuds_qt.utils.async_dialog import run_dialog_async
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.utils.qt_utils import blocked_signals, fill_combo_box, qt_error_handler
from openfreebuds_qt.designer.device_other import Ui_OfbQtDeviceOtherSettingsModule

LANGUAGE_OPTION_MAPPING = {
    "en-GB": "English (British)",
    "zh-CN": "Chinese"
}

SPATIAL_MODES = ["head_tracking", "fixed"]
SPATIAL_ROOMS = ["default", "theater", "cinema", "concert_hall"]
HEAD_ACTIONS = ["none", "answer", "reject"]
ADAPTIVE_VOLUME_LEVELS = ["low", "default", "high"]

BOX_TONE_VOLUME_DEBOUNCE_MS = 300

# Upload status uses stable state codes; only English source strings live here, display goes through self.tr()
UPLOAD_STATUS_TEXT = {
    "converting": "Preparing the sound…",
    "uploading": "Uploading… {0}%",
    "uploading_to_earbuds": "Uploading to earbuds…",
    "unsupported": "This device doesn't accept custom sounds.",
    "file_missing": "The audio file is missing.",
    "device_rejected": "The earbuds refused this sound, please retry.",
    "upload_failed": "Upload failed, please retry.",
    "failed": "Couldn't prepare the sound.",
    "done": "Upload finished.",
    "builtin": "Built-in sound selected.",
}


def _glyph_icon(glyph: str, color: QColor) -> QIcon:
    """Draw button icons with QPainter so they do not depend on fonts or emoji."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if glyph == "check":
        pen = QPen(color, 5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline(QPolygonF([
            QPointF(6, 17), QPointF(13, 24), QPointF(26, 8),
        ]))
    elif glyph == "play":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(QPolygonF([
            QPointF(8, 5), QPointF(27, 16), QPointF(8, 27),
        ]))
    elif glyph == "stop":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRect(QRectF(8, 8, 16, 16))
    painter.end()
    return QIcon(pixmap)


class OfbQtDeviceOtherSettingsModule(Ui_OfbQtDeviceOtherSettingsModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lang_options: list[str] = []

        self.spatial_mode_names = {
            "head_tracking": self.tr("Head tracking"),
            "fixed": self.tr("Fixed"),
        }
        self.spatial_room_names = {
            "default": self.tr("Default"),
            "theater": self.tr("Theater"),
            "cinema": self.tr("Cinema"),
            "concert_hall": self.tr("Concert hall"),
        }
        self.head_action_names = {
            "none": self.tr("No action"),
            "answer": self.tr("Answer call"),
            "reject": self.tr("Reject call"),
        }
        self.adaptive_volume_level_names = {
            "low": self.tr("Low"),
            "default": self.tr("Default"),
            "high": self.tr("High"),
        }

        self.setupUi(self)

        self.box_tone_volume_timer = QTimer(self)
        self.box_tone_volume_timer.setSingleShot(True)
        self.box_tone_volume_timer.setInterval(BOX_TONE_VOLUME_DEBOUNCE_MS)
        self.box_tone_volume_timer.timeout.connect(self.on_box_tone_lid_volume_commit)

        self.spatial_audio_toggle.toggled.connect(self.on_spatial_audio_toggle)
        self.spatial_audio_mode_box.currentIndexChanged.connect(self.on_spatial_mode_select)
        self.spatial_audio_room_box.currentIndexChanged.connect(self.on_spatial_room_select)
        self.adaptive_volume_toggle.toggled.connect(self.on_adaptive_volume_toggle)
        self.adaptive_volume_level_box.currentIndexChanged.connect(self.on_adaptive_volume_level_select)
        self.head_control_toggle.toggled.connect(self.on_head_control_toggle)
        self.head_nod_box.currentIndexChanged.connect(self.on_head_nod_select)
        self.head_shake_box.currentIndexChanged.connect(self.on_head_shake_select)
        self.drop_reminder_toggle.toggled.connect(self.on_drop_reminder_toggle)
        self.box_tone_toggle.toggled.connect(self.on_box_tone_toggle)
        self.box_tone_lid_toggle.toggled.connect(self.on_box_tone_lid_toggle)
        self.box_tone_lid_volume_slider.valueChanged.connect(self.on_box_tone_lid_volume_changed)
        # The progress bar appears only while a transfer is actually running
        self.box_tone_progress.setVisible(False)
        self.box_tone_progress.setFormat("%p%")
        # 'Prompt tone:' sits next to the selector with no spacer; the apply button has a fixed small size
        self.box_tone_pick_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.box_tone_pick_row.layout().setSpacing(2)
        self.box_tone_pick_row.layout().setStretch(1, 1)
        self.box_tone_apply.setMinimumWidth(96)
        self.box_tone_apply.setMaximumWidth(108)
        glyph_color = self.palette().buttonText().color()
        self.box_tone_apply.setText("")
        self.box_tone_apply.setToolTip(self.tr("Apply sound"))
        self.box_tone_apply.setIcon(_glyph_icon("check", glyph_color))
        self.box_tone_apply.setIconSize(QSize(14, 14))
        self.box_tone_apply.setFixedSize(30, 30)
        self.box_tone_preview.setText("")
        self.box_tone_preview.setToolTip(self.tr("Preview"))
        self.box_tone_preview.setIcon(_glyph_icon("play", glyph_color))
        self.box_tone_preview.setIconSize(QSize(14, 14))
        self.box_tone_preview.setFixedSize(30, 30)
        self._uploading = False
        self._headset_in_box = False
        self._master_enabled = False
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.setInterval(30000)
        self._status_timer.timeout.connect(self._clear_status_text)
        self._last_status = ""
        self._status_cleared = False
        self._preview_tmp = None
        self.box_tone_status.setOpenExternalLinks(False)
        self.box_tone_status.linkActivated.connect(self._open_link)
        self.box_tone_export_row.setVisible(False)
        self.box_tone_status.setVisible(False)
        self.box_tone_export_left.setOpenExternalLinks(False)
        self.box_tone_export_left.linkActivated.connect(self._open_link)
        self.box_tone_export_right.setOpenExternalLinks(False)
        self.box_tone_export_right.linkActivated.connect(self._open_link)

        # Local tone library: the UI only displays/triggers; all reads/writes go through ToneLibrary
        self.tone_library = ToneLibrary().ensure()
        self.tone_entries = []
        self.box_tone_select.currentIndexChanged.connect(self.on_tone_selection_changed)
        self.box_tone_preview.clicked.connect(self.on_box_tone_preview)
        self.box_tone_apply.clicked.connect(self.on_box_tone_apply)
        self.box_tone_add.clicked.connect(self.on_tone_add)
        self.box_tone_edit.clicked.connect(self.on_tone_edit)
        self.box_tone_delete.clicked.connect(self.on_tone_delete)
        self.box_tone_export.clicked.connect(self.on_tone_export)
        self.box_tone_sync_config.clicked.connect(self.on_tone_sync_config)
        self.box_tone_sync_audio.clicked.connect(self.on_tone_sync_audio)

        for button in (self.find_earbud_left, self.find_earbud_right, self.find_earbud_both):
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.setMinimumWidth(120)
        find_layout = self.find_earbud_buttons.layout()
        for index in range(find_layout.count()):
            find_layout.setStretch(index, 1)
        self.find_earbud_left.clicked.connect(lambda: self.on_find_earbud("left"))
        self.find_earbud_right.clicked.connect(lambda: self.on_find_earbud("right"))
        self.find_earbud_both.clicked.connect(lambda: self.on_find_earbud("both"))

    async def update_ui(self, event: OfbCoreEvent):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_UpdateUi", self.ctx):
            if event.kind_match(OfbEventKind.DEVICE_CHANGED):
                # Visibility setup
                auto_pause_visible = await self.ofb.get_property("config", "auto_pause") is not None
                low_latency_visible = await self.ofb.get_property("config", "low_latency") is not None
                service_language_visible = await self.ofb.get_property("service", "language") is not None
                spatial_audio_visible = await self.ofb.get_property(
                    "sound", "spatial_audio_supported") == "true"
                adaptive_volume_visible = await self.ofb.get_property(
                    "sound", "adaptive_volume_supported") == "true"
                head_control_visible = await self.ofb.get_property(
                    "config", "head_control_supported") == "true"
                drop_reminder_visible = await self.ofb.get_property(
                    "config", "drop_reminder_supported") == "true"
                box_tone_visible = (
                    await self.ofb.get_property("config", "box_tone_supported") == "true"
                    or await self.ofb.get_property("config", "box_tone_lid_supported") == "true"
                )

                self.auto_pause_root.setVisible(auto_pause_visible)
                self.low_latency_root.setVisible(low_latency_visible)
                self.service_language_root.setVisible(service_language_visible)
                self.spatial_audio_root.setVisible(spatial_audio_visible)
                self.adaptive_volume_root.setVisible(adaptive_volume_visible)
                self.head_control_root.setVisible(head_control_visible)
                self.drop_reminder_root.setVisible(drop_reminder_visible)
                self.box_tone_root.setVisible(box_tone_visible)

                self.list_item.setVisible(
                    auto_pause_visible or service_language_visible or low_latency_visible
                    or spatial_audio_visible or adaptive_volume_visible
                    or head_control_visible or drop_reminder_visible or box_tone_visible
                )

            if event.is_changed("config", "auto_pause"):
                with blocked_signals(self.auto_pause_toggle):
                    self.auto_pause_toggle.setChecked(await self.ofb.get_property("config", "auto_pause") == "true")

            if event.is_changed("config", "low_latency"):
                with blocked_signals(self.low_latency_toggle):
                    self.low_latency_toggle.setChecked(await self.ofb.get_property("config", "low_latency") == "true")
                    self.low_latency_toggle.setEnabled(True)

            if event.is_changed("service", "language_options"):
                options = await self.ofb.get_property("service", "language_options")
                if options is not None:
                    self.lang_options = options.split(",")
                    with blocked_signals(self.service_language_box):
                        self.service_language_box.clear()
                        self.service_language_box.addItems(
                            [LANGUAGE_OPTION_MAPPING.get(o, o) for o in self.lang_options]
                        )
                        self.service_language_box.setCurrentIndex(-1)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("sound", "spatial_audio"):
                spatial_enabled = await self.ofb.get_property("sound", "spatial_audio") == "true"
                with blocked_signals(self.spatial_audio_toggle):
                    self.spatial_audio_toggle.setChecked(spatial_enabled)
                self.spatial_audio_options.setEnabled(spatial_enabled)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("sound", "spatial_audio_mode"):
                current = await self.ofb.get_property("sound", "spatial_audio_mode")
                fill_combo_box(self.spatial_audio_mode_box, SPATIAL_MODES, self.spatial_mode_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("sound", "spatial_audio_room"):
                current = await self.ofb.get_property("sound", "spatial_audio_room")
                fill_combo_box(self.spatial_audio_room_box, SPATIAL_ROOMS, self.spatial_room_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("sound", "adaptive_volume"):
                adaptive_enabled = await self.ofb.get_property("sound", "adaptive_volume") == "true"
                with blocked_signals(self.adaptive_volume_toggle):
                    self.adaptive_volume_toggle.setChecked(adaptive_enabled)
                self.adaptive_volume_level_options.setEnabled(adaptive_enabled)

            if (event.kind_match(OfbEventKind.DEVICE_CHANGED)
                    or event.is_changed("sound", "adaptive_volume_level")
                    or event.is_changed("sound", "adaptive_volume_level_options")):
                level_options = await self.ofb.get_property("sound", "adaptive_volume_level_options")
                self.adaptive_volume_level_options.setVisible(level_options is not None)
                if level_options is not None:
                    current = await self.ofb.get_property("sound", "adaptive_volume_level")
                    fill_combo_box(self.adaptive_volume_level_box, level_options.split(","),
                                   self.adaptive_volume_level_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("config", "head_control_enabled"):
                head_enabled = await self.ofb.get_property("config", "head_control_enabled") == "true"
                with blocked_signals(self.head_control_toggle):
                    self.head_control_toggle.setChecked(head_enabled)
                self.head_control_options.setEnabled(head_enabled)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("config", "head_control_nod_action"):
                current = await self.ofb.get_property("config", "head_control_nod_action")
                fill_combo_box(self.head_nod_box, HEAD_ACTIONS, self.head_action_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("config", "head_control_shake_action"):
                current = await self.ofb.get_property("config", "head_control_shake_action")
                fill_combo_box(self.head_shake_box, HEAD_ACTIONS, self.head_action_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("config", "drop_reminder"):
                drop_enabled = await self.ofb.get_property("config", "drop_reminder") == "true"
                with blocked_signals(self.drop_reminder_toggle):
                    self.drop_reminder_toggle.setChecked(drop_enabled)

            if (event.kind_match(OfbEventKind.DEVICE_CHANGED)
                    or event.is_changed("config", "box_tone_enabled")
                    or event.is_changed("config", "box_tone_lid_enabled")
                    or event.is_changed("config", "box_tone_lid_supported")
                    or event.is_changed("config", "box_tone_lid_volume")
                    or event.is_changed("state", "headset_in_box")):
                master_enabled = await self.ofb.get_property("config", "box_tone_enabled") == "true"
                with blocked_signals(self.box_tone_toggle):
                    self.box_tone_toggle.setChecked(master_enabled)

                lid_supported = await self.ofb.get_property("config", "box_tone_lid_supported") == "true"
                headset_in_box = await self.ofb.get_property("state", "headset_in_box") == "true"

                with blocked_signals(self.box_tone_lid_toggle):
                    self.box_tone_lid_toggle.setChecked(
                        await self.ofb.get_property("config", "box_tone_lid_enabled") == "true")

                volume = await self.ofb.get_property("config", "box_tone_lid_volume")
                with blocked_signals(self.box_tone_lid_volume_slider):
                    if volume is not None:
                        try:
                            self.box_tone_lid_volume_slider.setValue(int(volume))
                        except ValueError:
                            pass
                    self.box_tone_lid_volume_value.setText(str(self.box_tone_lid_volume_slider.value()))

                self.box_tone_lid_options.setVisible(lid_supported)
                was_in_box = self._headset_in_box
                self._headset_in_box = headset_in_box
                self._master_enabled = master_enabled
                self.box_tone_toggle.setEnabled(headset_in_box)
                # When the master prompt tone is off, the lid-open tone controls are disabled too
                lid_controls_enabled = headset_in_box and master_enabled
                self.box_tone_lid_toggle.setEnabled(lid_controls_enabled)
                self.box_tone_lid_volume_slider.setEnabled(lid_controls_enabled)
                self.box_tone_lid_box_hint.setVisible(not headset_in_box)
                self._refresh_tone_enabled()

                # When both earbuds change from 'not in case' to 'both in case', re-read the current tone from the device and rebuild the combo
                if headset_in_box and not was_in_box:
                    await self.ofb.set_property("config", "box_tone_refresh", "1")
                    await self.refresh_tone_list()

            if (event.kind_match(OfbEventKind.DEVICE_CHANGED)
                    or event.is_changed("config", "box_tone_id")):
                await self.refresh_tone_list()

            if (event.is_changed("config", "box_tone_upload_status")
                    or event.is_changed("config", "box_tone_upload_progress")):
                await self.refresh_upload_status()

            if (event.kind_match(OfbEventKind.DEVICE_CHANGED)
                    or event.is_changed("state", "find_earbud_ringing")):
                await self.refresh_find_state()

    @asyncSlot(bool)
    async def on_low_latency_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetLowLatency", self.ctx):
            self.low_latency_toggle.setEnabled(False)
            await self.ofb.set_property("config", "low_latency", json.dumps(value))

    @asyncSlot(bool)
    async def on_auto_pause_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetAutoPause", self.ctx):
            await self.ofb.set_property("config", "auto_pause", json.dumps(value))

    @asyncSlot(int)
    async def on_language_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetLanguage", self.ctx):
            await self.ofb.set_property("service", "language", self.lang_options[index])

    @asyncSlot(bool)
    async def on_spatial_audio_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetSpatialAudio", self.ctx):
            self.spatial_audio_options.setEnabled(value)
            await self.ofb.set_property("sound", "spatial_audio", json.dumps(value))

    @asyncSlot(int)
    async def on_spatial_mode_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetSpatialMode", self.ctx):
            value = self.spatial_audio_mode_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("sound", "spatial_audio_mode", value)

    @asyncSlot(int)
    async def on_spatial_room_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetSpatialRoom", self.ctx):
            value = self.spatial_audio_room_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("sound", "spatial_audio_room", value)

    @asyncSlot(bool)
    async def on_adaptive_volume_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetAdaptiveVolume", self.ctx):
            await self.ofb.set_property("sound", "adaptive_volume", json.dumps(value))

    @asyncSlot(int)
    async def on_adaptive_volume_level_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetAdaptiveVolumeLevel", self.ctx):
            value = self.adaptive_volume_level_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("sound", "adaptive_volume_level", value)

    @asyncSlot(bool)
    async def on_head_control_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetHeadControl", self.ctx):
            self.head_control_options.setEnabled(value)
            await self.ofb.set_property("config", "head_control_enabled", json.dumps(value))

    @asyncSlot(int)
    async def on_head_nod_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetHeadNod", self.ctx):
            value = self.head_nod_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("config", "head_control_nod_action", value)

    @asyncSlot(int)
    async def on_head_shake_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetHeadShake", self.ctx):
            value = self.head_shake_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("config", "head_control_shake_action", value)

    @asyncSlot(bool)
    async def on_drop_reminder_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetDropReminder", self.ctx):
            await self.ofb.set_property("config", "drop_reminder", json.dumps(value))

    @asyncSlot(bool)
    async def on_box_tone_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetBoxTone", self.ctx):
            await self.ofb.set_property("config", "box_tone_enabled", json.dumps(value))

    @asyncSlot(bool)
    async def on_box_tone_lid_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetBoxToneLid", self.ctx):
            await self.ofb.set_property("config", "box_tone_lid_enabled", json.dumps(value))

    def on_box_tone_lid_volume_changed(self, value: int):
        self.box_tone_lid_volume_value.setText(str(value))
        self.box_tone_volume_timer.start()

    @asyncSlot()
    async def on_box_tone_lid_volume_commit(self):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetBoxToneVolume", self.ctx):
            volume = self.box_tone_lid_volume_slider.value()
            await self.ofb.set_property("config", "box_tone_lid_volume", str(volume))

    # ---- Tone library ------------------------------------------------

    async def refresh_tone_list(self):
        """Rebuild the combo: `id: *display name`; * marks the device's current box_tone_id."""
        self._hide_export_row()
        self.tone_entries = sorted(self.tone_library.entries(), key=lambda entry: entry.id)

        current = 0
        try:
            raw = await self.ofb.get_property("config", "box_tone_id")
            current = int(raw) if raw not in (None, "") else 0
        except (TypeError, ValueError):
            current = 0

        with blocked_signals(self.box_tone_select):
            self.box_tone_select.clear()
            for entry in self.tone_entries:
                name = get_prompt_tone_name(
                    entry, is_custom=not self.tone_library.is_editable(entry))
                star = "★ " if entry.id == current else ""
                self.box_tone_select.addItem(f"{entry.id}: {star}{name}", entry.id)
            index = self.box_tone_select.findData(current)
            if index >= 0:
                self.box_tone_select.setCurrentIndex(index)
        self._refresh_tone_enabled()

    async def refresh_upload_status(self):
        status = await self.ofb.get_property("config", "box_tone_upload_status") or ""
        progress = await self.ofb.get_property("config", "box_tone_upload_progress") or ""
        status_changed = status != self._last_status
        self._last_status = status
        if status_changed:
            self._status_cleared = False
        if status == "uploading":
            self._uploading = True
        elif status in ("done", "builtin", "upload_failed", "device_rejected", "failed", "file_missing", "unsupported"):
            self._uploading = False
        self._refresh_tone_enabled()

        if not status:
            # Empty state takes no row, avoiding a fake gap between the tone group and find-earbud group
            self.box_tone_status.setText("")
            self.box_tone_status.setVisible(False)
            self.box_tone_progress.setVisible(False)
            self._status_timer.stop()
            self._status_cleared = False
            return

        if self._status_cleared:
            # Terminal states that already auto-disappeared must not pop back on later refreshes
            return

        self._hide_export_row()
        self.box_tone_status.setVisible(True)
        self.box_tone_progress.setVisible(status == "uploading")
        if status == "uploading":
            try:
                percent = int(progress)
            except (TypeError, ValueError):
                percent = 0
            self.box_tone_progress.setValue(max(0, min(100, percent)))

        text = self.tr(UPLOAD_STATUS_TEXT.get(status, status))
        if status == "uploading":
            # Progress goes to the progress bar; text only says what is happening
            text = self.tr("Uploading to earbuds…")
        self.box_tone_status.setText(text)

        # Success/failure messages stay for 30 seconds then disappear; repeated refreshes of the same state do not reset the timer
        if status_changed and status in (
                "done", "builtin", "upload_failed", "device_rejected", "failed", "file_missing", "unsupported"):
            self._status_timer.start()
        elif not status:
            self._status_timer.stop()

    def _clear_status_text(self):
        self._status_cleared = True
        self.box_tone_status.setText("")
        self.box_tone_status.setVisible(False)

    def _refresh_tone_enabled(self):
        """Tone settings that touch the earbuds are allowed only when both earbuds are in the case."""
        in_box = getattr(self, "_headset_in_box", False)
        master = getattr(self, "_master_enabled", False)
        self.box_tone_toggle.setEnabled(in_box)
        self.box_tone_lid_toggle.setEnabled(in_box and master)
        self.box_tone_lid_volume_slider.setEnabled(in_box and master)
        self.box_tone_apply.setEnabled(in_box and not self._uploading)
        self.box_tone_select.setEnabled(not self._uploading)

        # Official tones are read-only: edit/delete follow the current selection and are disabled for them
        entry = None
        if hasattr(self, "tone_library"):
            entry = self._selected_tone()
        editable = bool(entry is not None and self.tone_library.is_editable(entry))
        self.box_tone_edit.setEnabled(editable)
        self.box_tone_delete.setEnabled(editable)
        self.box_tone_preview.setEnabled(
            bool(entry is not None and self.tone_library.has_pcm(entry)))

    def on_tone_selection_changed(self, _index: int):
        self._refresh_tone_enabled()

    def _selected_tone(self):
        tone_id = self.box_tone_select.currentData()
        if tone_id is None:
            return None
        return self.tone_library.find(int(tone_id))

    def on_box_tone_preview(self):
        """Preview the selected tone locally without going through the earbuds; clicking again while playing stops it."""
        try:
            from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
        except ImportError:
            return

        if hasattr(self, "_preview_player"):
            if self._preview_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self._preview_player.stop()
                return

        entry = self._selected_tone()
        if entry is None or not self.tone_library.has_pcm(entry):
            return

        fd, tmp_name = tempfile.mkstemp(suffix=".wav", prefix="ofb_tone_preview_")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            pcm = self.tone_library.pcm_path(entry).read_bytes()
            with wave.open(str(tmp_path), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16755)
                # Append 120 ms of silence so QMediaPlayer does not cut off the tail early
                w.writeframes(pcm + b"\x00\x00" * int(16755 * 0.12))
        except (OSError, ValueError) as e:
            tmp_path.unlink(missing_ok=True)
            self._warn(str(e))
            return

        if not hasattr(self, "_preview_player"):
            self._preview_player = QMediaPlayer(self)
            self._preview_output = QAudioOutput(self)
            self._preview_player.setAudioOutput(self._preview_output)
            self._preview_player.playbackStateChanged.connect(self._on_preview_state)

        self._preview_player.stop()
        self._preview_player.setSource(QUrl())
        if self._preview_tmp is not None:
            try:
                self._preview_tmp.unlink(missing_ok=True)
            except OSError:
                pass
        self._preview_tmp = tmp_path
        self._preview_player.setSource(QUrl.fromLocalFile(str(tmp_path)))
        self._preview_player.play()

    def _on_preview_state(self, state):
        from PyQt6.QtMultimedia import QMediaPlayer
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        color = self.palette().buttonText().color()
        if playing:
            self.box_tone_preview.setIcon(_glyph_icon("stop", color))
            self.box_tone_preview.setToolTip(self.tr("Stop preview"))
        else:
            self.box_tone_preview.setIcon(_glyph_icon("play", color))
            self.box_tone_preview.setToolTip(self.tr("Preview"))

    @asyncSlot()
    async def on_box_tone_apply(self):
        # While a previous transfer is still running (success or failure), apply does nothing
        if self._uploading:
            return
        if not self._headset_in_box:
            return
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_ApplyTone", self.ctx):
            entry = self._selected_tone()
            if entry is None:
                return

            self._uploading = True
            self._refresh_tone_enabled()
            try:
                # The handler may not be attached yet during a reconnect; do not let exceptions escape into qasync
                await self.ofb.set_property("config", "box_tone_id", str(entry.id))

                # Id 0 is the earbuds' real built-in tone (unfold/Unfold): write toneId=0, select=0 only, no audio transfer
                if entry.id == 0:
                    return

                if not self.tone_library.has_pcm(entry):
                    self.box_tone_status.setText(self.tr("This sound has no local audio file to send."))
                    return

                await self.ofb.set_property("config", "box_tone_upload", json.dumps({
                    "id": entry.id,
                    "path": str(self.tone_library.pcm_path(entry)),
                    "name": entry.name,
                }))
            except Exception:
                self.box_tone_status.setText(self.tr("Failed"))
            finally:
                self._uploading = False
                self._refresh_tone_enabled()

    @asyncSlot()
    async def on_tone_add(self):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_AddTone", self.ctx):
            path = await self._pick_audio_file(self.tr("Select audio file"))
            if not path:
                return

            with tempfile.TemporaryDirectory() as tmp:
                converted = Path(tmp) / "tone.pcm"
                try:
                    convert_to_tone_pcm(Path(path), converted)
                    samples = np.frombuffer(converted.read_bytes(), dtype="<i2")
                except (OSError, ValueError) as e:
                    self._warn(str(e))
                    return

                file_name = _ascii_file_name(Path(path).stem)
                dialog = OfbQtToneEditorDialog(self, samples, file_name, Path(path).stem)
                if not await run_dialog_async(dialog):
                    return

                try:
                    tone = self.tone_library.add(
                        dialog.processed().astype("<i2").tobytes(),
                        dialog.file_name,
                        dialog.display_name,
                    )
                except (ToneLibraryError, ValueError) as e:
                    self._warn(str(e))
                    return

            self.box_tone_status.setText(
                self.tr("Custom sound {0} added.").format(tone.id))
            await self.refresh_tone_list()

    @asyncSlot()
    async def on_tone_edit(self):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_EditTone", self.ctx):
            entry = self._selected_tone()
            if entry is None or not self.tone_library.is_editable(entry):
                return

            try:
                samples = np.frombuffer(self.tone_library.pcm_path(entry).read_bytes(), dtype="<i2")
            except (OSError, ValueError) as e:
                self._warn(str(e))
                return

            dialog = OfbQtToneEditorDialog(self, samples, entry.name, entry.display_name,
                                           samples.size / 16755.0)
            if not await run_dialog_async(dialog):
                return

            try:
                self.tone_library.update(
                    entry.id,
                    file_name=dialog.file_name,
                    display_name=dialog.display_name,
                    pcm=dialog.processed().astype("<i2").tobytes(),
                )
            except (ToneLibraryError, ValueError) as e:
                self._warn(str(e))
                return

            await self.refresh_tone_list()

    @asyncSlot()
    async def on_tone_delete(self):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_DeleteTone", self.ctx):
            entry = self._selected_tone()
            if entry is None or not self.tone_library.is_editable(entry):
                return

            dialog = QMessageBox(QMessageBox.Icon.Question,
                                 self.tr("Delete sound?"),
                                 self.tr("Will delete following sound:") + "\n"
                                 + get_prompt_tone_name(entry, is_custom=True),
                                 QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                                 self)
            dialog.setWindowModality(Qt.WindowModality.WindowModal)
            if not await run_dialog_async(dialog):
                return

            try:
                self.tone_library.delete(entry.id)
            except ToneLibraryError as e:
                self._warn(str(e))
                return
            await self.refresh_tone_list()

    @asyncSlot()
    async def on_tone_export(self):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_ExportTones", self.ctx):
            path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Export sounds as ZIP"),
                "prompt_tones.zip",
                "ZIP (*.zip)",
            )
            if not path:
                return
            try:
                target = self.tone_library.export_zip(Path(path))
            except (ToneLibraryError, OSError) as e:
                self._warn(str(e))
                return
            self._show_export_result(target)

    def _show_export_result(self, target: Path):
        """Export complete: file name on the left, 'Open containing folder' on the right, single line."""
        file_url = QUrl.fromLocalFile(str(target)).toString()
        folder_url = QUrl.fromLocalFile(str(target.parent)).toString()
        self.box_tone_status.setVisible(False)
        self.box_tone_export_left.setTextFormat(Qt.TextFormat.RichText)
        self.box_tone_export_left.setText(
            self.tr("Exported to {0}").format(
                f'<a href="{file_url}">{html_escape(target.name)}</a>'))
        self.box_tone_export_right.setTextFormat(Qt.TextFormat.RichText)
        self.box_tone_export_right.setText(
            f'<a href="{folder_url}">{html_escape(self.tr("Open folder"))}</a>')
        self.box_tone_export_row.setVisible(True)

    def _hide_export_row(self):
        self.box_tone_export_row.setVisible(False)
        self.box_tone_status.setVisible(bool(self.box_tone_status.text()))

    @asyncSlot()
    async def on_tone_sync_config(self):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SyncToneCatalog", self.ctx):
            try:
                result = self.tone_library.refresh_official_config()
            except (ToneLibraryError, OSError, ValueError) as e:
                self._warn(str(e))
                return
            self.box_tone_status.setText(
                self.tr("Official catalog: {0} total, {1} added, {2} updated.").format(
                    result.official_total, len(result.added), len(result.updated)))
            await self.refresh_tone_list()

    @asyncSlot()
    async def on_tone_sync_audio(self):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SyncToneAudio", self.ctx):
            try:
                result = self.tone_library.refresh_official_tones()
            except (ToneLibraryError, OSError, ValueError) as e:
                self._warn(str(e))
                return
            self.box_tone_status.setText(
                self.tr("Official audio: {0} files written.").format(len(result.pcm_written)))
            await self.refresh_tone_list()

    async def _pick_audio_file(self, title: str) -> str:
        # Use QFileDialog static functions: on Windows this always opens the native dialog.
        # Previously an instance + show() made Qt fall back to a custom dialog (the equalizer stays native because it intercepts differently).
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            self.tr("Audio files (*.wav *.mp3 *.m4a *.ogg *.flac *.pcm)"),
        )
        return path

    def _open_link(self, url: str):
        QDesktopServices.openUrl(QUrl(url))

    def _warn(self, message: str):
        dialog = QMessageBox(QMessageBox.Icon.Warning, self.tr("Failed"), message,
                             QMessageBox.StandardButton.Ok, self)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.show()

    # ---- Find earbud -------------------------------------------------

    async def refresh_find_state(self):
        ringing = await self.ofb.get_property("state", "find_earbud_ringing") or ""
        sides = [part for part in ringing.split(",") if part]

        self.find_earbud_left.setText(
            self.tr("Stop ringing") if "left" in sides else self.tr("Left earbud ring"))
        self.find_earbud_right.setText(
            self.tr("Stop ringing") if "right" in sides else self.tr("Right earbud ring"))
        self.find_earbud_both.setText(
            self.tr("Stop ringing") if sides else self.tr("Both earbuds ring"))

        if not sides:
            self.find_earbud_status.setText(self.tr("Not ringing"))
        elif "left" in sides and "right" in sides:
            self.find_earbud_status.setText(self.tr("Both earbuds are ringing"))
        elif "left" in sides:
            self.find_earbud_status.setText(self.tr("Left earbud is ringing"))
        else:
            self.find_earbud_status.setText(self.tr("Right earbud is ringing"))

    @asyncSlot()
    async def on_find_earbud(self, side: str):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_FindEarbud", self.ctx):
            ringing = await self.ofb.get_property("state", "find_earbud_ringing") or ""
            sides = [part for part in ringing.split(",") if part]
            active = bool(sides) if side == "both" else side in sides

            if active:
                # Stop ringing without confirmation
                await self._send_find_command(f"stop:{side}")
                return

            # Per-ear check: 0x2B25 p1/p2 already reports left/right, so warn only when the ear that will ring is worn
            worn = await self._is_worn(side)
            if worn:
                if not await self._confirm_worn():
                    return

            await self._send_find_command(f"ring:{side}")

    async def _is_worn(self, side: str) -> bool:
        """Whether the ear that will ring is currently worn; fall back to the global in_ear value when per-ear data is missing."""
        def as_bool(value) -> bool | None:
            if value == "true":
                return True
            if value == "false":
                return False
            return None

        left = as_bool(await self.ofb.get_property("battery", "left_in_ear"))
        right = as_bool(await self.ofb.get_property("battery", "right_in_ear"))

        if side == "left":
            if left is not None:
                return left
            return as_bool(await self.ofb.get_property("state", "in_ear")) is True
        if side == "right":
            if right is not None:
                return right
            return as_bool(await self.ofb.get_property("state", "in_ear")) is True
        if left is not None or right is not None:
            return bool(left) or bool(right)
        return as_bool(await self.ofb.get_property("state", "in_ear")) is True

    async def _send_find_command(self, command: str):
        # Do not throw link-down errors into qasync; show a failure message in the status bar
        try:
            await self.ofb.set_property("config", "find_earbud", command)
        except Exception:
            self.find_earbud_status.setText(self.tr("Failed"))
            return
        await self.refresh_find_state()

    async def _confirm_worn(self) -> bool:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle(self.tr("Earbuds are being worn"))
        dialog.setText(self.tr("The earbuds you are about to ring are being worn. "
                               "Loud sound at close range may damage your hearing. Ring anyway?"))
        ring_button = dialog.addButton(self.tr("Ring anyway"), QMessageBox.ButtonRole.AcceptRole)
        cancel_button = dialog.addButton(self.tr("Cancel"), QMessageBox.ButtonRole.RejectRole)
        ring_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        dialog.setDefaultButton(cancel_button)
        dialog.setEscapeButton(cancel_button)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        return await run_dialog_async(dialog)


def _ascii_file_name(stem: str) -> str:
    """Compress any file name into an ASCII name allowed by the library (letters/digits/spaces/underscores/hyphens)."""
    cleaned = "".join(ch if ch.isascii() and (ch.isalnum() or ch in " _-") else " " for ch in stem)
    cleaned = " ".join(cleaned.split()).strip(" _-")[:32]
    return cleaned or "tone"
